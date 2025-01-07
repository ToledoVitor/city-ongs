from datetime import datetime
from fpdf import FPDF
from fpdf.enums import XPos, YPos

class PassToThird(FPDF):

    def header(self):
        # Título
        self.set_font("Helvetica", "B", 12)
        self.cell(
            0,
            10,
            "ANEXO RP-10 - REPASSES AO TERCEIRO SETOR",
            align="C",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT
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

    def footer(self):
        # Rodapé
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.cell(0, 10, f"Page {self.page_no()}", align="C")

    def add_text(self, text, bold):
        if bold == True:
            self.bold = "B"
        else: 
            self.bold = ""
        self.set_font("Helvetica", self.bold, 9)
        self.cell(40, 10, text, align="L")
        self.ln(2)

    def add_table(self, headers, rows):
        # Tabela do cabeçalho
        self.set_font("Helvetica", "B", 9)
        for header in headers:
            self.cell(40, 10, header, border=1, align="C")
        self.ln()  # Move to the next line after the header row

        # Linhas das colunas
        self.set_font("Helvetica", "", 9)
        for row in rows:
            for col in row:
                self.cell(40, 10, str(col), border=1, align="C")
            self.ln()  # Move to the next line after each row


# Create PDF object
pdf = PassToThird()
pdf.add_page()

# Dados da Organização
pdf.add_text("Órgão Público", True)
pdf.add_text("Prefeitura Municipal de Várzea Paulista", False)
pdf.add_text("Organização da Sociedade Civil", True)
pdf.add_text("Associação Comunidade Varzina - Eco & Vida (Meio Ambiente)", False)
pdf.add_text("CNPJ", True)
pdf.add_text("02.834.119/0001-95", False)
pdf.add_text("Endereço e CEP", True)
pdf.add_text("Rua Feres Sada 82 - Loteamento Parque Empresarial São Luís", False)
pdf.add_text("Responsáveis pela OSC", True)
# "Nome, Papel, CPF")

# Dados da parceria
pdf.add_text("Objeto da Parceria", "Executar a coleta de recicláveis no município de Várzea Paulista - SP")
pdf.add_text("Exercício", "01/11/2024 a 30/11/2024")
pdf.add_text("Origem dos Recursos (1)", "Consolidado de todas as fontes")

# Tabela "DOCUMENTO"
headers = ["DOCUMENTO", "DATA", "VIGÊNCIA", "VALOR - R$"]
rows = [
    ["Termo de Colaboração nº 10/2023", "26/09/2023", "26/09/2023 - 26/09/2024", "R$ 761.992,32"],
    ["Aditamento Nº 1", "25/09/2024", "26/09/2024 - 25/09/2025", "R$ 776.193,00"],
]
pdf.add_table(headers, rows)

# Tabela "DEMONSTRATIVO DOS RECURSOS"
pdf.add_text("DEMONSTRATIVO DOS RECURSOS DISPONÍVEIS NO EXERCÍCIO", "B")
headers = [
    "DATA PREVISTA PARA O REPASSE (2)",
    "VALORES PREVISTOS (R$)",
    "DATA DO REPASSE",
    "NÚMERO DO DOCUMENTO DE CRÉDITO",
    "VALORES REPASSADOS (R$)",
]
rows = [["10/2024", "64.682,75", "05/11/2024", "552766000230001", "64.682,75"]]
pdf.add_table(headers, rows)

# Resumo
pdf.add_text("(A) SALDO DO EXERCÍCIO ANTERIOR", False)
pdf.add_text("R$ 42.554,87", False)
pdf.add_text("(B) REPASSES PÚBLICOS NO EXERCÍCIO", False)
pdf.add_text("R$ 64.682,75", False)
pdf.add_text("(C) RECEITAS COM APLICAÇÕES FINANCEIRAS DOS REPASSES PÚBLICOS", False)
pdf.add_text("R$ 0,00", False)
pdf.add_text("(D) OUTRAS RECEITAS DECORRENTES DA EXECUÇÃO DO AJUSTE (3)", False)
pdf.add_text("R$ 0,00", False)
pdf.add_text("(E) TOTAL DE RECURSOS PÚBLICOS (A + B + C + D)", False)
pdf.add_text("R$ 107.237,62", False)
pdf.add_text("(F) RECURSOS PRÓPRIOS DA ENTIDADE PARCEIRA", False)
pdf.add_text("R$ 0,00", False)
pdf.add_text("(G) TOTAL DE RECURSOS DISPONÍVEIS NO EXERCÍCIO (E + F)", False)
pdf.add_text("R$ 107.237,62", False)

# Save the PDF
pdf.output(f"rp10-{str(datetime.now().time())[0:8]}.pdf")
