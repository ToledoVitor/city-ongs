import xlsxwriter
from datetime import datetime


# Updated upstream
def export_accountability_csv():
    # 1. Pegar campos no banco
    # 2. Anaisar e transformar campos
    # 3. Gerar arquivo xlsx
    # 4. Retornar arquivo

    prefeitura = "Várzea Pta"

    # Create a workbook and add a worksheet.
    workbook = xlsxwriter.Workbook("Expenses01.xlsx")
    worksheet = workbook.add_worksheet()

    expenses = (
        ["Banana", 20],
        ["Mac", 22],
        ["Pera", 30],
    )

    row = 0
    col = 0

    for item, id in expenses:
        worksheet.write(row, col, item)
        worksheet.write(row, col + 1, id)
        row += 1

    worksheet.write(row, 0, "Total")
    worksheet.write(row, 1, "=SUM(B1:B3)")


# =======
def _build_receipt_worksheet(workbook):
    receipt_worksheet = workbook.add_worksheet(name="1. RECEITAS")

    # Formatação células cabeçalho (linha 1)
    header_format = workbook.add_format(
        {
            "bold": True,
            # 'border':   6,
            "align": "center",
            "valign": "vcenter",
            "fg_color": "#a3d7c6",
        }
    )

    # Formatação células sub título (linha 2)
    sub_format = workbook.add_format(
        {
            "align": "center",
            "valign": "vcenter",
            "fg_color": "#efe920",
        }
    )

    # Criando cabeçalho
    header_content = (
        ["ID DO PROJETO", "", ""],
        ["IDENTIFICAÇÃO", "", ""],
        ["VALOR", "", ""],
        ["VENCIMENTO", "", ""],
        ["COMPETÊNCIA", "", ""],
        ["FONTE DE RECURSO", "Nome", "ID (não preencher)"],
        ["CONTA BANCÁRIA", "Nome", "ID (não preencher)"],
        ["NATUREZA DA RECEITA", "Nome", "ID (não preencher)"],
        ["OBSERVAÇÕES", "", ""],
    )

    col = 0
    for main_colum, sub1, sub2 in header_content:
        if sub1 == "":
            # Adiciona texto e mesclas células 1 e 2 de suas respectivas colunas
            receipt_worksheet.merge_range(0, col, 1, col, main_colum, header_format)

        else:
            # Adiciona sub coluna mescla colunas de acordo com o seu título
            receipt_worksheet.merge_range(0, col, 0, col + 1, main_colum, header_format)
            receipt_worksheet.write(1, col, sub1, sub_format)
            receipt_worksheet.write(1, col + 1, sub2, sub_format)
            col += 1

        col += 1

    receipt_worksheet.autofit()
    return receipt_worksheet


def _build_expense_worksheet(workbook):
    content = [""]

    expense_worksheet = workbook.add_worksheet(name="2. DESPESAS")
    # PREENCHER AQUI

    return expense_worksheet


def _build_application_worksheet(workbook):
    content = [""]

    application_worksheet = workbook.add_worksheet(name="3. APLICACOES E RESGATES")
    # PREENCHER AQUI

    return application_worksheet


def _build_fr_worksheet(workbook):
    content = [""]

    fr_worksheet = workbook.add_worksheet(name="FR")
    # PREENCHER AQUI

    return fr_worksheet


def _build_bank_account_worksheet(workbook):
    content = [""]

    bank_account_worksheet = workbook.add_worksheet(name="CB")
    # PREENCHER AQUI

    return bank_account_worksheet


def _build_category_worksheet(workbook):
    content = [""]

    category_worksheet = workbook.add_worksheet(name="NR")
    # PREENCHER AQUI

    return category_worksheet


def _build_expense_category_worksheet(workbook):
    content = [""]

    expense_category_worksheet = workbook.add_worksheet(name="ND")
    # PREENCHER AQUI

    return expense_category_worksheet


def _build_favored_worksheet(workbook):
    content = [""]

    favored_worksheet = workbook.add_worksheet(name="FV")
    # PREENCHER AQUI

    return favored_worksheet


def _build_ia_worksheet(workbook):
    content = [""]

    ia_worksheet = workbook.add_worksheet(name="IA")
    # PREENCHER AQUI

    return ia_worksheet


def _build_doc_type_worksheet(workbook):
    content = [""]

    doc_type_worksheet = workbook.add_worksheet(name="TD")
    # PREENCHER AQUI

    return doc_type_worksheet


def _build_pr_worksheet(workbook):
    content = [""]

    pr_worksheet = workbook.add_worksheet(name="PR")
    # PREENCHER AQUI

    return pr_worksheet


def export_accountability_csv():
    # Criar modelo de Fornecedor

    prefeitura = "Várzea Pta"
    archive = f"archive-{str(datetime.now().time())[0:8]}.xlsx"

    # Configurações de formatação básica

    # Cria planilha e abas.
    workbook = xlsxwriter.Workbook(archive)

    receipt_worksheet = _build_receipt_worksheet(workbook)
    expense_worksheet = _build_expense_worksheet(workbook)
    application_worksheet = _build_application_worksheet(workbook)
    fr_worksheet = _build_fr_worksheet(workbook)
    bank_account_worksheet = _build_bank_account_worksheet(workbook)
    category_worksheet = _build_category_worksheet(workbook)
    expense_category_worksheet = _build_expense_category_worksheet(workbook)
    favored_worksheet = _build_favored_worksheet(workbook)
    ia_worksheet = _build_ia_worksheet(workbook)
    doc_type_worksheet = _build_doc_type_worksheet(workbook)
    pr_worksheet = _build_pr_worksheet(workbook)

    workbook.close()

    return workbook


if __name__ == "__main__":
    export_accountability_csv()
