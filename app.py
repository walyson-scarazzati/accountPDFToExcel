import csv
import io
import re
import subprocess
import tempfile
from pathlib import Path

import camelot
import streamlit as st


ACCOUNTING_HEADERS = [
    "DATA ",
    "VALOR",
    "DEBITO ",
    "CRÉDITO ",
    "CÓDIGO DO HISTÓRICO ",
    "COMPLEMENTO ",
]


def is_good_enough(table):
    report = table.parsing_report
    return report["accuracy"] > 80.0 and report["whitespace"] < 25.0


def extract_tables(pdf_path):
    lattice_tables = camelot.read_pdf(
        pdf_path, flavor="lattice", process_background=True, pages="1-end"
    )
    stream_tables = camelot.read_pdf(pdf_path, flavor="stream", pages="1-end")

    selected = []
    if lattice_tables and stream_tables and len(lattice_tables) == len(stream_tables):
        for lattice, stream in zip(lattice_tables, stream_tables):
            lattice_report = lattice.parsing_report
            stream_report = stream.parsing_report
            same_location = (
                lattice_report["page"] == stream_report["page"]
                and lattice_report["order"] == stream_report["order"]
            )

            if is_good_enough(lattice) and is_good_enough(stream) and same_location:
                selected.append(lattice if lattice.df.size >= stream.df.size else stream)
            elif is_good_enough(lattice):
                selected.append(lattice)
            elif is_good_enough(stream):
                selected.append(stream)
    else:
        source = lattice_tables if len(lattice_tables) >= len(stream_tables) else stream_tables
        selected = list(source)

    return sorted(
        (table for table in selected if table.df.shape[0] > 0),
        key=lambda table: (table.page, -table._bbox[3]),
    )


def parse_statement_amount(value):
    value = value.replace("@", "0").replace("O", "0").replace("o", "0")
    comma_amounts = re.findall(r"\d[\d.]*,\d{2}", value)
    if comma_amounts:
        amount = comma_amounts[0]
        integer, cents = amount.replace(".", "").split(",")
    else:
        if not re.search(r"\d[\d.]*\.\d{2}\s*[CD]", value, re.IGNORECASE):
            return None
        amount = re.findall(r"\d[\d.]*\.\d{2}", value)[-1]
        integer, cents = amount.rsplit(".", 1)
        integer = integer.replace(".", "")

    integer = f"{int(integer):,}".replace(",", ".")
    return f"R$ {integer},{cents}"


def accounting_rows(pdf_path):
    rows = []
    skipped = 0
    result = subprocess.run(
        ["pdftotext", "-layout", "-nopgbrk", str(pdf_path), "-"],
        capture_output=True,
        text=True,
        check=True,
    )

    def save_transaction(transaction):
        nonlocal skipped
        if not transaction:
            return

        complement = " ".join(transaction["complement"]).strip()
        if re.search(
            r"\b(saldo|lote|documento|valor)\b|hist[oó]rico|histdrico",
            complement,
            re.IGNORECASE,
        ):
            return

        amount = parse_statement_amount(transaction["amount"])
        if not amount:
            skipped += 1
            amount = ""

        rows.append(
            [
                transaction["date"],
                amount,
                "",
                "",
                "",
                complement,
            ]
        )

    text = result.stdout

    year_match = re.search(
        r"(?:janeiro|fevereiro|março|marco|abril|maio|junho|julho|agosto|setembro|outubro|novembro|dezembro)/(\d{4})",
        text,
        re.IGNORECASE,
    )
    statement_year = year_match.group(1) if year_match else None

    # Restrict parsing to the account-movement ledger, so tables that appear
    # later in the statement (indices, contracts, investments...) and that
    # may also contain dates and amounts are not mistaken for transactions.
    ledger_start = re.search(r"Movimenta[çc][ãa]o\b", text)
    ledger_end = re.search(r"Saldos por Per[íi]odo", text)
    if ledger_start:
        text = text[ledger_start.end() : ledger_end.start() if ledger_end else None]

    amount_pattern = re.compile(r"\d[\d.]*,\d{2}|\d[\d.]*\.\d{2}\s*[CD]\b", re.IGNORECASE)

    current_date = None
    current = None
    for line in text.splitlines():
        date_match = re.match(r"^\s*(\d{2}/\d{2}(?:/\d{4})?)\s+(.*)$", line)
        if date_match:
            date, body = date_match.groups()
            if len(date) == 5 and statement_year:
                date = f"{date}/{statement_year}"
            current_date = date
        else:
            body = line

        if not amount_pattern.search(body):
            if current and line.strip() and len(line) - len(line.lstrip()) >= 30:
                current["complement"].append(re.sub(r"\s+", " ", line).strip())
            continue

        if current_date is None:
            continue

        if re.search(r"\b(saldo|lote|documento)\b|hist[oó]rico", body, re.IGNORECASE):
            continue

        save_transaction(current)

        amount_match = re.search(r"\d[\d.]*,\d{2}", body)
        if amount_match:
            amount = amount_match.group()
        else:
            dot_amount = re.search(r"(\d[\d.]*\.\d{2})\s*([CD])", body, re.IGNORECASE)
            amount = f"{dot_amount.group(1)} {dot_amount.group(2)}" if dot_amount else ""
        description = body
        if amount:
            description = description[: description.find(amount.split()[0])]
        description = re.sub(r"^\s*\d{4}\s+\d{4,5}\s+\d{3}\s*", "", description)
        description = re.sub(r"\s+\d[\d.]*\s*$", "", description).strip()
        current = {
            "date": current_date,
            "amount": amount,
            "complement": [description] if description else [],
        }

    save_transaction(current)
    return rows, skipped


def accounting_csv(rows):
    output = io.StringIO(newline="")
    writer = csv.writer(output, delimiter=";", lineterminator="\r\n")
    writer.writerow(ACCOUNTING_HEADERS)
    writer.writerows(rows)
    return output.getvalue().encode("utf-8-sig")


def ocr_pdf(pdf_path, output_path):
    command = [
        "ocrmypdf",
        "--force-ocr",
        "--deskew",
        "--rotate-pages",
        "--clean",
        "--optimize",
        "0",
        str(pdf_path),
        str(output_path),
    ]
    return subprocess.run(command, capture_output=True, text=True)


st.set_page_config(page_title="PDF para Excel", page_icon="📄", layout="wide")
st.title("PDF para Excel")
st.write("Envie um PDF e converta as tabelas em uma planilha Excel.")

uploaded_file = st.file_uploader("Selecione um arquivo PDF", type=["pdf"])

if uploaded_file:
    run_ocr = st.checkbox(
        "Forcar OCR antes da conversao",
        value=True,
        help="Refaz o reconhecimento, inclusive quando o texto existente no PDF esta corrompido.",
    )

    if st.button("Converter para Excel", type="primary"):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            source_path = temp_path / uploaded_file.name
            source_path.write_bytes(uploaded_file.getvalue())

            processing_path = source_path
            status = st.status("Processando PDF...", expanded=True)

            with status:
                if run_ocr:
                    st.write("Executando OCR...")
                    ocr_path = temp_path / f"{source_path.stem}-ocr.pdf"
                    result = ocr_pdf(source_path, ocr_path)
                    if result.returncode in (0, 6) and ocr_path.exists():
                        processing_path = ocr_path
                        st.write("OCR concluido.")
                    else:
                        st.warning("OCR indisponivel ou falhou; tentando ler o PDF original.")
                        if result.stderr:
                            st.caption(result.stderr[:500])

                st.write("Detectando tabelas...")
                try:
                    tables = extract_tables(str(processing_path))
                except Exception as exc:
                    st.error(f"Nao foi possivel converter o PDF: {exc}")
                    tables = []

                if not tables:
                    st.error("Nenhuma tabela foi encontrada.")
                else:
                    status.update(label="Conversao concluida", state="complete")

                    st.success(f"{len(tables)} tabela(s) encontrada(s).")

                    for index, table in enumerate(tables, start=1):
                        with st.expander(f"Tabela {index} - pagina {table.page}", expanded=index == 1):
                            st.dataframe(table.df, use_container_width=True)

                    try:
                        rows, skipped = accounting_rows(str(processing_path))
                    except (FileNotFoundError, subprocess.CalledProcessError) as exc:
                        st.error(f"Não foi possível preparar o CSV contábil: {exc}")
                    else:
                        if rows:
                            st.download_button(
                                "Baixar CSV contábil",
                                data=accounting_csv(rows),
                                file_name=f"{source_path.stem}.csv",
                                mime="text/csv",
                            )
                            st.info(
                                "DÉBITO, CRÉDITO e CÓDIGO DO HISTÓRICO ficaram vazios "
                                "para preenchimento. Confira os dados extraídos antes de importar."
                            )
                            if skipped:
                                st.warning(
                                    f"{skipped} lançamento(s) foram incluídos sem valor legível; "
                                    "revise a coluna VALOR."
                                )
                        else:
                            st.warning(
                                "Não foi possível organizar os lançamentos deste PDF no formato contábil."
                            )
