from datetime import datetime

from fpdf import FPDF, XPos, YPos
from fpdf.fonts import FontFace


class Expenses(FPDF):
    def header(self):
        # Cabeçalho e títulos
        self.set_margins(15, 10, 15)
        self.set_font("Helvetica", "B", 11)
        self.cell(
            0,
            0,
            "DESPESAS REALIZADAS DO PERÍODO",
            align="C",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        self.set_font("Helvetica", "", 10)
        self.cell(
            0,
            10,
            "Período: 01/11/2024 à 30/11/2024",
            align="C",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        # Espaçamento do título pro próximo dado
        self.set_y(self.get_y() + 5)

    def footer(self):
        # Rodapé
        self.set_y(-15)
        self.set_font("Helvetica", "I", 7)
        self.cell(0, 10, f"Page {self.page_no()}", align="C")
        self.cell(0, 10, str(datetime.now().time())[0:8], align="R")


# Gera PDF
pdf = FPDF()
pdf = Expenses()
pdf.add_page(orientation="L")
cell_height = 5

# Dados da Organização
pdf.set_font("Helvetica", "", 7)
pdf.set_fill_color(233, 234, 236)
pdf.primary_color: tuple = (48, 84, 150)
pdf.cell(
    text="**Órgão Concessor:** Prefeitura Municipal de Várzea Paulista",
    markdown=True,
    h=cell_height,
)
pdf.ln(4)
pdf.cell(
    text="**Tipo de Concessão:** Termo de Colaboração",
    markdown=True,
    h=cell_height,
)
pdf.ln(4)
pdf.cell(text="**Nº:** 10/2023", markdown=True, h=cell_height)
pdf.ln(4)
pdf.cell(
    text="**Entidade Beneficiária:** Associação Comunidade Varzina - Eco & Vida (Meio Ambiente)",
    markdown=True,
    h=cell_height,
)
pdf.ln(4)
pdf.cell(text="**CNPJ:** 02.834.119/0001-95", markdown=True, h=cell_height)
pdf.ln(4)
pdf.cell(
    text="**Endereço:** Rua Feres Sada 82 - Loteamento Parque Empresarial São Luís",
    markdown=True,
    h=cell_height,
)
pdf.ln(4)
pdf.cell(
    text="**Objeto:** Executar a coleta de recicláveis no município de Várzea Paulista - SP, em acordo com a Política Nacional de Resíduos Sólidos (PNRS)",
    markdown=True,
    h=cell_height,
)

# Tabela Dados da Conta
pdf.ln(8)
pdf.set_font("Helvetica", "B", 8)
pdf.cell(text="Dados da Conta", markdown=True, align="L", h=cell_height)
pdf.ln(4)

# First colunms are used to align the grey space with the letter D, seconds are the grey space.
account_data = [
    ["", "", "", "**Conta:** CONTA CORRENTE"],
    ["", "", "", "**Banco:** Banco do Brasil S.A."],
    ["", "", "", "**Agência:** 2766-9"],
    ["", "", "", "**Nº da Conta:** 45578-4"],
    [
        "",
        "",
        "",
        "**Fontes de Recurso:** Prefeitura Municipal de Várzea Paulista | Associação Comunidade Varzina - Eco & Vida (Social) |",
    ],
]

col_widths = [1, 1, 4, 259]
pdf.set_font("Helvetica", "", 7)
for row_index, row in enumerate(account_data):
    for col_index, col_text in enumerate(row):
        if col_index == 1:
            pdf.cell(
                col_widths[col_index],
                h=cell_height,
                text=col_text,
                align="C",
                markdown=True,
                fill=True,
            )
        else:
            pdf.cell(
                col_widths[col_index],
                h=cell_height,
                text=col_text,
                align="L",
                markdown=True,
            )
    pdf.ln(4)

# Tabela Repasses
pdf.ln(8)
pdf.set_font("Helvetica", "B", 8)
pdf.cell(text="Repasses", markdown=True, align="L", h=cell_height)
pdf.ln(4)

headers = ["Repasse", "Valor", "Data Dcto.", "Competência", "Recebimento"]
table_data = [
    [
        "Repasse Publico",
        "R$ 64.682,75",
        "05/11/2024",
        "31/10/2024",
        "05/11/2024",
    ],
]

header_style = FontFace(emphasis="BOLD", size_pt=10)
cell_style = FontFace(size_pt=10)

col_widths = [59, 52, 52, 52, 52]

pdf.set_font("Helvetica", "B", 7)
for col_index, header in enumerate(headers):
    text_align = "C"
    if col_index == 0:
        text_align = "L"
    pdf.cell(
        col_widths[col_index],
        h=cell_height,
        text=header,
        border="LRT",
        align=text_align,
        fill=True,
    )
pdf.ln()

for row in table_data:
    for col_index, col_text in enumerate(row):
        text_align = "C"
        if col_index == 0:
            text_align = "L"
        if col_index == 1:
            text_align = "R"
        pdf.cell(
            col_widths[col_index],
            h=cell_height,
            text=col_text,
            border="LR",
            align=text_align,
        )
    pdf.ln()

pdf.cell(sum(col_widths), h=0, border="T")

# Table: EXPENSES
pdf.ln(8)
pdf.set_font("Helvetica", "B", 8)
pdf.cell(text="Despesas", markdown=True, align="L", h=cell_height)
pdf.ln(4)

table_data = [
    (
        "Item",
        "Comptência",
        "Tipo",
        "Nº do Documento",
        "Favorecido",
        "Identificação da Despesa",
        "Forma de Liquidação",
        "Data de Liquidação",
        "Nº Docto. Vinculado",
        "Valor",
    )
]
table_data.extend(
    [
        (
            "1",
            "31/10/2024",
            "NF-E",
            "249",
            "CONTABILIDADE PILOTO E SILVA SOCIEDADE SIMPLES LTDA",
            "Contabilidade",
            "Transferência Eletrônica",
            "05/11/2024",
            "110501",
            "3.000,00",
        ),
        (
            "2",
            "31/10/2024",
            "NFS-E",
            "18",
            "ALLAN GOLÇALVES DE CARVALHO",
            "Administrativo",
            "Transferência Eletrônica",
            "05/11/2024",
            "110502",
            "6.000,00",
        ),
        (
            "3",
            "31/10/2024",
            "NFS-E",
            "50",
            "DIRCELIO TIMOTIO DOS SANTOS",
            "Contrapartida",
            "Transferência Eletrônica",
            "05/11/2024",
            "110503",
            "2.500,00",
        ),
        (
            "4",
            "31/10/2024",
            "NFS-E",
            "20",
            "REGINALDO ROSSI",
            "Caminhão",
            "Transferência Eletrônica",
            "06/11/2024",
            "110601",
            "2.500,00",
        ),
        (
            "5",
            "31/10/2024",
            "NFS-E",
            "19",
            "CLAUDINEIA GONÇALO DOS SANTOS",
            "Caminhão",
            "Transferência Eletrônica",
            "06/11/2024",
            "110602",
            "6.500,00",
        ),
        (
            "4",
            "31/10/2024",
            "NFS-E",
            "20",
            "REGINALDO ROSSI",
            "Caminhão",
            "Transferência Eletrônica",
            "06/11/2024",
            "110601",
            "2.500,00",
        ),
        (
            "5",
            "31/10/2024",
            "NFS-E",
            "19",
            "CLAUDINEIA GONÇALO DOS SANTOS",
            "Caminhão",
            "Transferência Eletrônica",
            "06/11/2024",
            "110602",
            "6.500,00",
        ),
        (
            "1",
            "31/10/2024",
            "NF-E",
            "249",
            "CONTABILIDADE PILOTO E SILVA SOCIEDADE SIMPLES LTDA",
            "Contabilidade",
            "Transferência Eletrônica",
            "05/11/2024",
            "110501",
            "3.000,00",
        ),
        (
            "2",
            "31/10/2024",
            "NFS-E",
            "18",
            "ALLAN GOLÇALVES DE CARVALHO",
            "Administrativo",
            "Transferência Eletrônica",
            "05/11/2024",
            "110502",
            "6.000,00",
        ),
        (
            "3",
            "31/10/2024",
            "NFS-E",
            "50",
            "DIRCELIO TIMOTIO DOS SANTOS",
            "Contrapartida",
            "Transferência Eletrônica",
            "05/11/2024",
            "110503",
            "2.500,00",
        ),
        (
            "4",
            "31/10/2024",
            "NFS-E",
            "20",
            "REGINALDO ROSSI",
            "Caminhão",
            "Transferência Eletrônica",
            "06/11/2024",
            "110601",
            "2.500,00",
        ),
        (
            "5",
            "31/10/2024",
            "NFS-E",
            "19",
            "CLAUDINEIA GONÇALO DOS SANTOS",
            "Caminhão",
            "Transferência Eletrônica",
            "06/11/2024",
            "110602",
            "6.500,00",
        ),
        (
            "4",
            "31/10/2024",
            "NFS-E",
            "20",
            "REGINALDO ROSSI",
            "Caminhão",
            "Transferência Eletrônica",
            "06/11/2024",
            "110601",
            "2.500,00",
        ),
        (
            "5",
            "31/10/2024",
            "NFS-E",
            "19",
            "CLAUDINEIA GONÇALO DOS SANTOS",
            "Caminhão",
            "Transferência Eletrônica",
            "06/11/2024",
            "110602",
            "6.500,00",
        ),
    ]
)

headings_style = FontFace(emphasis="BOLD", size_pt=8, fill_color=(233, 234, 236))

with pdf.table(
    borders_layout="NO_HORIZONTAL_LINES",
    headings_style=headings_style,
    line_height=6,
    align="C",
    col_widths=(10, 25, 10, 20, 85, 25, 30, 25, 20, 15),
) as table:
    pdf.set_font("Helvetica", "", 6)
    for data_row in table_data:
        pdf.set_fill_color(255, 255, 255)
        row = table.row()
        for datum in data_row:
            row.cell(datum, align="C")


# pdf.cell(text="Segunda-feira, 6 de Janeiro de 2025", align="R", h=cell_height)
pdf.ln(10)
pdf.set_font("Helvetica", "", 8)
pdf.cell(text="Responsáveis pela Contratada:", h=cell_height)

pdf.output(f"expenses-{str(datetime.now().time())[0:8]}.pdf")
