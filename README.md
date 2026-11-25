# PDF para Excel

Aplicação em Python para localizar tabelas em arquivos PDF e organizar seus dados em uma interface web com Streamlit.

O projeto usa [Camelot](https://camelot-py.readthedocs.io/) para detectar tabelas, [OCRmyPDF](https://ocrmypdf.readthedocs.io/) para melhorar PDFs escaneados e `pdftotext` para preparar dados contábeis a partir de extratos bancários.

## Funcionalidades

- Envio de PDFs pela interface web
- Detecção de tabelas com os métodos `lattice` e `stream`
- OCR opcional antes da análise
- Prévia das tabelas encontradas
- Exportação de lançamentos bancários em CSV no formato contábil
- Colunas de débito, crédito e código do histórico deixadas vazias para revisão
- Exportação antiga por linha de comando para arquivos Excel

## Requisitos

- macOS
- Python 3.10
- Ghostscript
- Poppler
- Tesseract OCR
- OCRmyPDF
- Unpaper

No macOS, instale as ferramentas do sistema com o Homebrew:

```bash
brew install python@3.10 ghostscript poppler tesseract ocrmypdf unpaper
```

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

Quando o projeto reconhecer lançamentos bancários, será exibido um botão para baixar o CSV contábil. Os dados extraídos devem ser conferidos antes do uso contábil.

## Formato do CSV contábil

O arquivo usa o separador ponto e vírgula (`;`) e possui estas colunas:

| Coluna | Conteúdo |
| --- | --- |
| `DATA` | Data do lançamento |
| `VALOR` | Valor no formato `R$ 1.234,56` |
| `DEBITO` | Campo vazio para preenchimento |
| `CRÉDITO` | Campo vazio para preenchimento |
| `CÓDIGO DO HISTÓRICO` | Campo vazio para preenchimento |
| `COMPLEMENTO` | Descrição do lançamento |

## Conversão por linha de comando

O script `pdf_to_excel.py` percorre uma pasta em busca de PDFs, executa o OCR e tenta exportar as tabelas encontradas:

```bash
python pdf_to_excel.py /caminho/para/a/pasta
```

Se nenhum diretório for informado, o script processa o diretório atual.

## Observações

- A precisão da extração depende da qualidade do PDF, da presença de bordas nas tabelas e da resolução do texto.
- PDFs escaneados podem exigir OCR e ajustes de inclinação.
- PDFs complexos podem não preservar corretamente a divisão entre linhas e colunas.
- O CSV contábil foi desenvolvido para extratos bancários, mas não substitui a conferência manual dos dados.