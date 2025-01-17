from datetime import datetime

from fpdf import FPDF, XPos, YPos
from fpdf.fonts import FontFace


class Consolidated(FPDF):
    def header(self):
        # Cabeçalho e títulos
        self.set_margins(15, 10, 15)
        self.set_font("Helvetica", "B", 12)
        self.cell(
            0,
            0,
            "Consolidado das Conciliações Bancárias",
            align="C",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        # Espaçamento do título pro próximo dado
        self.set_y(self.get_y() + 2)

    def footer(self):
        # Rodapé
        self.set_y(-15)
        self.set_font("Helvetica", "I", 7)
        self.cell(0, 10, f"Page {self.page_no()}", align="C")
        self.cell(0, 10, str(datetime.now().time())[0:8], align="R")


def bank_statement(bs_pdf, bs_data, bs_col_widths, bs_headings_style):
    if bs_data != []:
        with pdf.table(
            borders_layout="NO_HORIZONTAL_LINES",
            headings_style=bs_headings_style,
            line_height=6,
            align="L",
            col_widths=bs_col_widths,
        ) as table:
            (bs_pdf.set_fill_color(255, 255, 255),)
            bs_pdf.set_font("Helvetica", "", 6)
            total = 0
            for data_row in bs_data:
                row = table.row()
                for datum_index, datum_text in enumerate(data_row):
                    text_align = "L"
                    if datum_index == 1:
                        text_align = "C"
                    if datum_index == 2:
                        text_align = "R"
                        total += float(datum_text)
                    row.cell(datum_text, align=text_align)
        return total
    else:
        pass


def general_vision(bs_pdf, bs_data, bs_col_widths, bs_headings_style):
    with pdf.table(
        borders_layout="NO_HORIZONTAL_LINES",
        headings_style=bs_headings_style,
        line_height=6,
        align="L",
        col_widths=bs_col_widths,
        markdown=True,
    ) as table:
        (bs_pdf.set_fill_color(255, 255, 255),)
        sub_data = [("Data", "Histórico", "Valor")]
        for sub_data_row in sub_data:
            row = table.row()
            for datum_index, datum_text in enumerate(sub_data_row):
                row.cell(datum_text, align="L")

        (bs_pdf.set_fill_color(255, 255, 255),)
        bs_pdf.set_font("Helvetica", "", 6)
        total = 0
        for data_row in bs_data:
            row = table.row()
            for datum_index, datum_text in enumerate(data_row):
                text_align = "L"
                if datum_index == 2:
                    total += float(datum_text)
                    text_align = "R"
                row.cell(datum_text, align=text_align)
    return total


# Gera PDF
pdf = FPDF()
pdf = Consolidated()
pdf.add_page()
cell_height = 5
pdf.set_draw_color(230, 230, 230)
pdf.set_fill_color(233, 234, 236)

pdf.set_font("Helvetica", "B", 8)
# First colunms are used to align the grey space with the letter D, seconds are the grey space.
account_data = [
    [
        "",
        "",
        "",
        "**Projeto:** TC 10/2023 - Associação Comunidade Varzina Educacional, Cultural e Comunicação Social",
    ],
    ["", "", "", "**Período Conciliado:** 01/11/2024 a 30/11/2024"],
    ["", "", "", "**Banco:** Banco do Brasil S.A."],
    ["", "", "", "**Conta:** 45578-4"],
    ["", "", "", "**Agência:** 2766-9"],
]

col_widths = [1, 1, 4, 184]
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

pdf.ln(10)
pdf.set_font("Helvetica", "B", 14)
pdf.cell(0, 0, "Extrato Bancário", align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

pdf.ln(cell_height)
pdf.set_font("Helvetica", "B", 8)
pdf.cell(180, cell_height, "Saldos Anteriores", align="L", fill=True, border="LR")
pdf.ln(cell_height)

data = [("CONTA CORRENTE", "(+)", "3370.09"), ("CONTA INVESTIMENTO", "(+)", "900.00")]
col_widths = (80, 90, 20)
headings_style = FontFace(size_pt=6)
total = bank_statement(pdf, data, col_widths, headings_style)

if data != []:
    headings_style = FontFace("Helvetica", "B", size_pt=6, fill_color=(233, 234, 236))
    data = [("Total dos Saldos Anteriores", "", str(total))]
    bank_statement(pdf, data, col_widths, headings_style)

pdf.set_font("Helvetica", "B", 8)
pdf.set_fill_color(233, 234, 236)
pdf.cell(
    180,
    cell_height,
    "Aplicações e Resgates dos Recursos Financeiros",
    align="L",
    fill=True,
    border="LR",
)
pdf.ln(cell_height)

data = []
col_widths = (80, 90, 20)
headings_style = FontFace(size_pt=6)
total = bank_statement(pdf, data, col_widths, headings_style)

if data != []:
    headings_style = FontFace("Helvetica", "B", size_pt=6, fill_color=(233, 234, 236))
    data = [
        ("Total das Aplicações e Resgates dos Recursos Financeiros", "", str(total))
    ]
    bank_statement(pdf, data, col_widths, headings_style)

pdf.set_font("Helvetica", "B", 8)
pdf.set_fill_color(233, 234, 236)
pdf.cell(
    180,
    cell_height,
    "Agrupamento das Receitas por Natureza de Receita",
    align="L",
    fill=True,
    border="LR",
)
pdf.ln(cell_height)

data = [
    (
        "Reembolso de Juros, multas, glosas, pagto. Indevido, duplicidade etc",
        "(+)",
        "1190.00",
    ),
    ("Repasse Público", "(+)", "64682.75"),
]
col_widths = (80, 90, 20)
headings_style = FontFace(size_pt=6)
total = bank_statement(pdf, data, col_widths, headings_style)

pdf.set_font("Helvetica", "B", 8)
pdf.set_fill_color(233, 234, 236)
pdf.cell(180, cell_height, "Despesas", align="L", fill=True, border="LR")
pdf.ln(cell_height)

data = [
    ("Despesas Planejadas - Previstas no Plano de Trabalho", "(-)", "68893.81"),
    (
        "Despesas Não Planejadas \n Desconsiderando despesas com investimento (IOF, IR, etc)",
        "(-)",
        "0",
    ),
]
col_widths = (80, 90, 20)
headings_style = FontFace(size_pt=6)
total = bank_statement(pdf, data, col_widths, headings_style)

if data != []:
    headings_style = FontFace("Helvetica", "B", size_pt=6, fill_color=(233, 234, 236))
    data = [("Total das Despesas", "", str(total))]
    bank_statement(pdf, data, col_widths, headings_style)

pdf.set_font("Helvetica", "B", 8)
pdf.set_fill_color(233, 234, 236)
pdf.cell(
    180,
    cell_height,
    "Transferências Bancárias para outras contas",
    align="L",
    fill=True,
    border="LR",
)
pdf.ln(cell_height)

data = [("Entradas", "(+)", "0.00"), ("Saidas", "(-)", "0.00")]
col_widths = (80, 90, 20)
headings_style = FontFace(size_pt=6)
total = bank_statement(pdf, data, col_widths, headings_style)

pdf.set_font("Helvetica", "B", 8)
pdf.set_fill_color(233, 234, 236)
pdf.cell(180, cell_height, "Saldos Finais", align="L", fill=True, border="LR")
pdf.ln(cell_height)

data = [("CONTA CORRENTE", "(+)", "349.43"), ("CONTA INVESTIMENTO BB", "(-)", "0.00")]
col_widths = (80, 90, 20)
headings_style = FontFace(size_pt=6)
total = bank_statement(pdf, data, col_widths, headings_style)

if data != []:
    headings_style = FontFace("Helvetica", "B", size_pt=6, fill_color=(233, 234, 236))
    data = [("Total dos Saldos Disponíveis(Bancos)", "", str(total))]
    bank_statement(pdf, data, col_widths, headings_style)

headings_style = FontFace("Helvetica", "B", size_pt=6, fill_color=(233, 234, 236))
data = [
    (
        "Saldo Final Calculado \n Este saldo deverá ser igual ao Total dos Saldos Disponíveis (Banco)",
        "",
        str(total),
    )
]
bank_statement(pdf, data, col_widths, headings_style)

pdf.set_font("Helvetica", "B", 9)
pdf.cell(180, cell_height, "", align="C", border="LR")
pdf.ln()
pdf.set_font("Helvetica", "B", 9)
pdf.set_fill_color(233, 234, 236)
pdf.cell(
    180,
    cell_height,
    "Visão Analítica dos Lançamentos",
    align="C",
    fill=True,
    border="LR",
)
pdf.ln(cell_height)

pdf.set_font("Helvetica", "B", 8)
pdf.set_fill_color(233, 234, 236)
pdf.cell(
    180,
    cell_height,
    "Reembolso de Juros, multas, glosas, pagto. Indevido, duplicidade etc",
    align="L",
    fill=True,
    border="LR",
)
pdf.ln(cell_height)

data = [
    (
        f"{str(datetime.now().time())[0:8]}",
        "**Banco:** TRANSFERÊnCIA RECEBIDA-22/1109:56ASSOCIACAOCOMUNIDADEVA \n **Sistema:** Devolução",
        "1190.00",
    )
]
col_widths = (80, 90, 20)
headings_style = FontFace("Helvetica", "B", size_pt=6)
total = general_vision(pdf, data, col_widths, headings_style)

headings_style = FontFace("Helvetica", "B", size_pt=6, fill_color=(233, 234, 236))
data = [("", "", str(total))]
bank_statement(pdf, data, col_widths, headings_style)

pdf.set_font("Helvetica", "B", 8)
pdf.set_fill_color(233, 234, 236)
pdf.cell(180, cell_height, "Repasse Público", align="L", fill=True, border="LR")
pdf.ln(cell_height)

data = [
    (
        f"{str(datetime.now().time())[0:8]}",
        "**Banco:** TRANSFERÊNCIARECEBIDA-05/1111:39PREFEITURAMDEVPAULIS \n **Sistema:** Repasse Público",
        "64682.75",
    )
]
col_widths = (80, 90, 20)
headings_style = FontFace("Helvetica", "B", size_pt=6)
total = general_vision(pdf, data, col_widths, headings_style)

headings_style = FontFace("Helvetica", "B", size_pt=6, fill_color=(233, 234, 236))
data = [("", "", str(total))]
bank_statement(pdf, data, col_widths, headings_style)

pdf.set_font("Helvetica", "B", 8)
pdf.set_fill_color(233, 234, 236)
pdf.cell(
    180,
    cell_height,
    "Reembolso de Juros, multas, glosas, pagto. Indevido, duplicidade etc",
    align="L",
    fill=True,
    border="LR",
)
pdf.ln(cell_height)

data = [
    (
        f"{str(datetime.now().time())[0:8]}",
        "**Banco:** TRANSFERÊnCIA RECEBIDA-22/1109:56ASSOCIACAOCOMUNIDADEVA \n **Sistema:** Devolução",
        "1190.00",
    )
]
col_widths = (80, 90, 20)
headings_style = FontFace("Helvetica", "B", size_pt=6)
total = general_vision(pdf, data, col_widths, headings_style)

headings_style = FontFace("Helvetica", "B", size_pt=6, fill_color=(233, 234, 236))
data = [("", "", str(total))]
bank_statement(pdf, data, col_widths, headings_style)

pdf.set_font("Helvetica", "B", 8)
pdf.set_fill_color(233, 234, 236)
pdf.cell(180, cell_height, "Repasse Despesas", align="L", fill=True, border="LR")
pdf.ln(cell_height)

data = [
    (
        f"{str(datetime.now().time())[0:8]}",
        "**Banco:** PIX-ENVIADO-05/1115:25CONTABILIDADEPSSSLME \n **Sistema:** Contabilidade",
        "3000.75",
    ),
    (
        f"{str(datetime.now().time())[0:8]}",
        "**Banco:** PIX-ENVIADO-05/1115:25CONTABILIDADEPSSSLME \n **Sistema:** Contrapartida",
        "6000.95",
    ),
    (
        f"{str(datetime.now().time())[0:8]}",
        "**Banco:** PIX-ENVIADO-05/1115:25CONTABILIDADEPSSSLME \n **Sistema:** Combustivel",
        "1840.15",
    ),
    (
        f"{str(datetime.now().time())[0:8]}",
        "**Banco:** PIX-ENVIADO-05/1115:25CONTABILIDADEPSSSLME \n **Sistema:** Vale Transporte",
        "300.00",
    ),
    (
        f"{str(datetime.now().time())[0:8]}",
        "**Banco:** PIX-ENVIADO-05/1115:25CONTABILIDADEPSSSLME \n **Sistema:** Holerite",
        "400.00",
    ),
    (
        f"{str(datetime.now().time())[0:8]}",
        "**Banco:** PIX-ENVIADO-05/1115:25CONTABILIDADEPSSSLME \n **Sistema:** Caminhão",
        "500.75",
    ),
]
col_widths = (80, 90, 20)
headings_style = FontFace("Helvetica", "B", size_pt=6)
total = general_vision(pdf, data, col_widths, headings_style)

headings_style = FontFace("Helvetica", "B", size_pt=6, fill_color=(233, 234, 236))
data = [("", "", str(total))]
bank_statement(pdf, data, col_widths, headings_style)

pdf.output(f"consolidated-{str(datetime.now().time())[0:8]}.pdf")
