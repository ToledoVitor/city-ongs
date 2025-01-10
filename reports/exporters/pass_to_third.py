from datetime import datetime

from fpdf import FPDF, XPos, YPos
from fpdf.fonts import FontFace


class PassToThird(FPDF):
    def header(self):
        # Cabeçalho e títulos
        self.set_margins(10, 15, 10)
        self.set_font("Helvetica", "B", 11)
        self.cell(
            0,
            0,
            "ANEXO RP-10 - REPASSES AO TERCEIRO SETOR",
            align="C",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        self.set_font("Helvetica", "", 10)
        self.cell(
            0,
            10,
            "DEMONSTRATIVO INTEGRAL DAS RECEITAS E DESPESAS - TERMO DE COLABORAÇÃO/FOMENTO",
            align="C",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        # Espaçamento do título pro próximo dado
        self.set_y(self.get_y() + 5)

    def footer(self):
        # Rodapé
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.cell(0, 10, f"Page {self.page_no()}", align="C")


# Gera PDF
pdf = PassToThird()
pdf.add_page()
cell_height = 5

# Dados da Organização
pdf.set_font("Helvetica", "", 8)
pdf.set_fill_color(233, 234, 236)
pdf.cell(
    text="**Órgão Público:** Prefeitura Municipal de Várzea Paulista",
    markdown=True,
    h=cell_height,
)
pdf.ln(4)
pdf.cell(
    text="**Organização da Sociedade Civil:** Associação Com unidade Varzina - Eco & Vida (Meio Ambiente)",
    markdown=True,
    h=cell_height,
)
pdf.ln(4)
pdf.cell(text="**CNPJ**: 02.834.119/0001-95", markdown=True, h=cell_height)
pdf.ln(4)
pdf.cell(
    text="**Endereço e CEP:** Rua Feres Sada 82 - Loteamento Parque Empresarial São Luís",
    markdown=True,
    h=cell_height,
)
pdf.ln(4)
pdf.cell(text="**Responsáveis pela OSC:**", markdown=True, h=cell_height)
pdf.ln(4)

# Tabela 1
pdf.set_font("Helvetica", "B", 7)
table_data = [
    ["Nome", "Papel", "CPF"],
]

col_widths = [70, 60, 60]

for row_index, row in enumerate(table_data):
    for col_index, col_text in enumerate(row):
        pdf.cell(
            col_widths[col_index], h=cell_height, text=col_text, border=1, align="L"
        )
    pdf.ln()

# Dados da parceria
pdf.ln(3)
pdf.set_font("Helvetica", "", 8)
pdf.cell(
    text="**Objeto da Parceria:** Executar a coleta de recicláveis no município de Várzea Paulista - SP",
    markdown=True,
    h=cell_height,
)
pdf.ln(4)
pdf.cell(text="**Exercício:** 01/11/2024 a 30/11/2024", markdown=True, h=cell_height)
pdf.ln(4)
pdf.cell(
    text="**Origem dos Recursos (1):** Consolidado de todas as fontes",
    markdown=True,
    h=cell_height,
)
pdf.ln(3)

# Tabela DOCUMENTO
pdf.set_font("Helvetica", "B", 7)
pdf.ln()
headers = ["DOCUMENTO", "DATA", "VIGÊNCIA", "VALOR - R$"]
table_data = [
    [
        "Termo de Colaboração nº 10/2023",
        "26/09/2023",
        "26/09/2023 - 26/09/2024",
        "R$ 761.992,32",
    ],
    ["Aditamento Nº 1", "25/09/2024", "26/09/2024 - 25/09/2025", "R$ 776.193,00"],
]

header_style = FontFace(emphasis="BOLD", size_pt=10)
cell_style = FontFace(size_pt=10)

col_widths = [75, 19, 65, 31]

pdf.set_font("Helvetica", "B", 8)
for col_index, header in enumerate(headers):
    pdf.cell(col_widths[col_index], h=cell_height, text=header, border=1, align="C")
pdf.ln()

pdf.set_font("Helvetica", "", 7)
for row in table_data:
    for col_index, col_text in enumerate(row):
        pdf.cell(
            col_widths[col_index], h=cell_height, text=col_text, border=1, align="C"
        )
    pdf.ln()

# Tabela "DEMONSTRATIVO DOS RECURSOS"
pdf.ln(6)

# Título
pdf.set_font("Helvetica", "B", 8)
pdf.cell(
    190,
    h=cell_height,
    text="DEMONSTRATIVO DOS RECURSOS DISPONÍVEIS NO EXERCÍCIO",
    border=1,
    align="C",
)
pdf.ln(cell_height)

# Cabeçalho
headers = [
    "DATA PREVISTA PARA O REPASSE (2)",
    "VALORES PREVISTOS (R$)",
    "DATA DO REPASSE",
    "NÚMERO DO DOCUMENTO DE CRÉDITO",
    "VALORES REPASSADOS (R$)",
]
table_data = [
    [
        "10/2024",
        "64.682,75",
        "05/11/2024",
        "552766000230001",
        "64.682,75",
    ],
]
header_style = FontFace(emphasis="BOLD", size_pt=10)
cell_style = FontFace(size_pt=10)
col_widths = [40, 35, 25, 50, 40]

pdf.set_font("Helvetica", "B", 8)
for col_index, header in enumerate(headers):
    x = pdf.get_x()
    y = pdf.get_y()
    pdf.multi_cell(col_widths[col_index], 4, header, border=1, align="C")
    pdf.set_xy(x + col_widths[col_index], y)
pdf.ln(8)

pdf.set_font("Helvetica", "", 7)
for row in table_data:
    for col_index, col_text in enumerate(row):
        if col_index == 4:
            pdf.cell(
                col_widths[col_index], h=cell_height, text=col_text, border=1, align="R"
            )
        else:
            pdf.cell(
                col_widths[col_index], h=cell_height, text=col_text, border=1, align="C"
            )
    pdf.ln()

# Linha cinza
pdf.cell(190, h=cell_height, text="", border=1, align="C", fill=True)
pdf.ln(cell_height)

# Tabela resumo
extern_revenue_data = [
    ["(A) SALDO DO EXERCÍCIO ANTERIOR", "", "R$ 42.554,87"],
    ["(B) REPASSES PÚBLICOS NO EXERCÍCIO", "", "R$ 64.682,75"],
    ["(C) RECEITAS COM APLICAÇÕES FINANCEIRAS DOS REPASSES PÚBLICOS", "", "R$ 0,00"],
    ["(D) OUTRAS RECEITAS DECORRENTES DA EXECUÇÃO DO AJUSTE (3)", "", "R$ 0,00"],
    ["(E) TOTAL DE RECURSOS PÚBLICOS (A + B + C + D)", "", "R$ 107.237,62"],
    ["", "", ""],
]
intern_revenue_data = [
    ["(F) RECURSOS PRÓPRIOS DA ENTIDADE PARCEIRA", "", "R$ 0,00"],
    ["(G) TOTAL DE RECURSOS DISPONÍVEIS NO EXERCÍCIO (E + F)", "", "R$ 107.237,62"],
]

pdf.set_font("Helvetica", "", 7)
col_widths = [100, 50, 40]

for row in extern_revenue_data:
    for col_index, col_text in enumerate(row):
        if col_index == 2:
            pdf.cell(
                col_widths[col_index], h=cell_height, text=col_text, border=1, align="R"
            )
        else:
            pdf.cell(
                col_widths[col_index], h=cell_height, text=col_text, border=1, align="L"
            )
    pdf.ln()

for row_index, row in enumerate(intern_revenue_data):
    for col_index, col_text in enumerate(row):
        if col_index == 2:
            pdf.cell(
                col_widths[col_index], h=cell_height, text=col_text, border=1, align="R"
            )
        else:
            pdf.cell(
                col_widths[col_index], h=cell_height, text=col_text, border=1, align="L"
            )
    if row_index != len(intern_revenue_data) - 1:
        pdf.ln()

# Rodapé do Relatório
pdf.ln(cell_height)
pdf.set_font("Helvetica", "", 7)
pdf.cell(
    text="(1) Verba: Federal, Estadual ou Municipal, devendo ser elaborado um anexo para cada fonte de recurso.",
    h=cell_height,
)
pdf.ln(3)
pdf.cell(
    text="(2) Incluir valores previstos no exercício anterior e repassados neste exercício.",
    h=cell_height,
)
pdf.ln(3)
pdf.cell(text="(3) Receitas com estacionamento, aluguéis, entre outras.", h=cell_height)

# Salva PDF
pdf.output(f"rp10-{str(datetime.now().time())[0:8]}.pdf")
