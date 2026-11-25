# PDF para Excel

Aplicação em Python para localizar tabelas em arquivos PDF e organizar seus dados em uma interface web com Streamlit.

O projeto usa [Camelot](https://camelot-py.readthedocs.io/) para detectar tabelas, [OCRmyPDF](https://ocrmypdf.readthedocs.io/) para melhorar PDFs escaneados e `pdftotext` para preparar dados a partir de extratos.

## Funcionalidades

- Envio de PDFs pela interface web
- Detecção de tabelas com os métodos `lattice` e `stream`
- OCR opcional antes da análise

## Requisitos
- Python 3.10
- Ghostscript
- Poppler
- Tesseract OCR
- OCRmyPDF
- Unpaper


## Instalação

Na pasta do projeto, crie um ambiente virtual e instale as dependências:

```bash
python3.10 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Como usar a interface web

Inicie o Streamlit:

```bash
streamlit run app.py
```

Abra `http://localhost:8501`, selecione um arquivo PDF e clique em **Converter para Excel**.

Antes da conversão, o OCR pode ser habilitado ou desabilitado:

- Habilitado: recomendado para PDFs escaneados ou imagens
- Desabilitado: recomendado quando o PDF já possui texto legível

## Conversão por linha de comando

O script `pdf_to_excel.py` percorre uma pasta em busca de PDFs, executa o OCR e tenta exportar as tabelas encontradas:

```bash
python pdf_to_excel.py /caminho/para/a/pasta
```

Se nenhum diretório for informado, o script processa o diretório atual.
