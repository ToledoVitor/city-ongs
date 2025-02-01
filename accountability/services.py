from io import BytesIO

import xlsxwriter

from accountability.models import Accountability, Expense, Revenue
from contracts.choices import NatureChoices
from contracts.models import Contract, Organization


class AccountabilityCSVExporter:
    workbook: None

    def __init__(self, accountability: Accountability):
        self.accountability: Accountability = accountability
        self.contract: Contract = accountability.contract
        self.organization: Organization = accountability.contract.organization
        self.contract_code: int = accountability.contract.internal_code

    def handle(self):
        output = BytesIO()

        self.workbook = xlsxwriter.Workbook(output, {"in_memory": True})
        self._build_worksheets()
        self.workbook.define_name("fr_tab", "FR!$A$2:$A$100")
        self.workbook.define_name("cb_tab", "CB!$A$2:$A$100")
        self.workbook.define_name("nr_tab", "NR!$A$2:$A$100")
        self.workbook.define_name("nd_tab", "ND!$A$2:$A$100")
        self.workbook.define_name("fv_tab", "FV!$A$2:$A$100")
        self.workbook.define_name("ia_tab", "IA!$A$2:$A$100")
        self.workbook.define_name("td_tab", "TD!$A$2:$A$100")
        self.workbook.define_name("pr_tab", "PR!$A$2:$A$100")
        self.workbook.close()

        output.seek(0)
        return output

    def _build_worksheets(self):
        builders = [
            self.__build_receipt_worksheet,
            self.__build_expense_worksheet,
            self.__build_application_worksheet,
            self.__build_revenue_worksheet,
            self.__build_bank_account_worksheet,
            self.__build_nature_category_worksheet,
            self.__build_expense_category_worksheet,
            self.__build_favored_worksheet,
            self.__build_ia_worksheet,
            self.__build_doc_type_worksheet,
            self.__build_pr_worksheet,
        ]

        for builder in builders:
            builder()

    def __build_receipt_worksheet(self):
        receipt_worksheet = self.workbook.add_worksheet(name="1. RECEITAS")

        header_format = self.workbook.add_format(
            {
                "bold": True,
                "border": 2,
                "align": "center",
                "valign": "vcenter",
                "fg_color": "#a3d7c6",
            }
        )
        header_breaking_line_format = self.workbook.add_format(
            {
                "bold": True,
                "border": 2,
                "align": "center",
                "valign": "vcenter",
                "fg_color": "#a3d7c6",
                "text_wrap": True,
            }
        )
        body_format = self.workbook.add_format(
            {
                "align": "center",
                "valign": "vcenter",
                "border": 1,
            }
        )
        locked_cell_format = self.workbook.add_format(
            {
                "align": "center",
                "valign": "vcenter",
                "border": 1,
                "bg_color": "#cfcdcd",
                "locked": True,
            }
        )

        header_content = (
            [" CÓDIGO DO CONTRATO ", header_breaking_line_format],
            [" IDENTIFICAÇÃO ", header_format],
            [" VALOR ", header_format],
            [" VENCIMENTO ", header_format],
            [" COMPETÊNCIA ", header_format],
            ["FONTE DE RECURSO", header_breaking_line_format],
            ["CONTA BANCÁRIA", header_breaking_line_format],
            ["NATUREZA DA RECEITA", header_breaking_line_format],
            [" OBSERVAÇÕES ", header_format],
        )

        col = 0
        for main_colum in header_content:
            receipt_worksheet.merge_range(0, col, 1, col, main_colum[0], main_colum[1])
            col += 1

        for line in range(2, 1002):
            receipt_worksheet.write(
                line, 0, self.contract_code, locked_cell_format
            )  # Coluna A
            receipt_worksheet.write(line, 1, "", body_format)  # Column B
            receipt_worksheet.write(line, 2, "", body_format)  # Column C
            receipt_worksheet.write(line, 3, "", body_format)  # Column D
            receipt_worksheet.write(line, 4, "", body_format)  # Column E

            # Column F
            receipt_worksheet.write(line, 5, "", locked_cell_format)
            receipt_worksheet.data_validation(
                line,
                5,
                self.contract_code,
                5,
                {
                    "validate": "list",
                    "source": "=fr_tab",
                    "input_message": "Escolha da lista",
                    "error_message": "Favor selecionar um dos itens listados ao clicar em  ▽  ao lado da célula",
                },
            )

            # Column G
            receipt_worksheet.write(line, 6, "", locked_cell_format)
            receipt_worksheet.data_validation(
                line,
                6,
                self.contract_code,
                6,
                {
                    "validate": "list",
                    "source": "=cb_tab",
                    "input_message": "Escolha da lista",
                    "error_message": "Favor selecionar um dos itens listados ao clicar em  ▽  ao lado da célula",
                },
            )

            # Column H
            receipt_worksheet.write(line, 7, "", locked_cell_format)
            receipt_worksheet.data_validation(
                line,
                7,
                self.contract_code,
                7,
                {
                    "validate": "list",
                    "source": "=nr_tab",
                    "input_message": "Escolha da lista",
                    "error_message": "Favor selecionar um dos itens listados ao clicar em  ▽  ao lado da célula",
                },
            )
            receipt_worksheet.write(line, 8, "", body_format)  # Column I

        receipt_worksheet.autofit()
        return receipt_worksheet

    def __build_expense_worksheet(self):
        expense_worksheet = self.workbook.add_worksheet(name="2. DESPESAS")

        header_format = self.workbook.add_format(
            {
                "bold": True,
                "border": 2,
                "align": "center",
                "valign": "vcenter",
                "fg_color": "#a3d7c6",
            }
        )
        header_breaking_line_format = self.workbook.add_format(
            {
                "bold": True,
                "border": 2,
                "align": "center",
                "valign": "vcenter",
                "fg_color": "#a3d7c6",
                "text_wrap": True,
            }
        )
        sub_format = self.workbook.add_format(
            {
                "align": "center",
                "valign": "vcenter",
                "fg_color": "#efe920",
                "border": 2,
                "text_wrap": True,
            }
        )
        body_format = self.workbook.add_format(
            {
                "align": "center",
                "valign": "vcenter",
                "border": 1,
            }
        )
        locked_cell_format = self.workbook.add_format(
            {
                "align": "center",
                "valign": "vcenter",
                "border": 1,
                "bg_color": "#cfcdcd",
                "locked": True,
            }
        )
        header_content = (
            [" ID DO PROJETO ", "", "", header_breaking_line_format],
            [" IDENTIFICAÇÃO ", "", "", header_format],
            [" VALOR ", "", "", header_format],
            [" VENCIMENTO ", "", "", header_format],
            [" COMPETÊNCIA ", "", "", header_format],
            [" FONTE DE RECURSO ", "", "", header_breaking_line_format],
            [
                " NATUREZA DA DESPESA (somente para despesa NÃO planejada)",
                "",
                "",
                header_breaking_line_format,
            ],
            [" FAVORECIDO/CONTRATADO", "Nome", "CPF/CNPJ", header_format],
            [
                "ITEM DE AQUISIÇÃO (somente despesa planejada)",
                "",
                "",
                header_breaking_line_format,
            ],
            [" TIPO DE DOCUMENTO", "", "", header_breaking_line_format],
            [" Nº DO DOCUMENTO ", "", "", header_format],
            [" OBSERVAÇÕES ", "", "", header_format],
        )

        col = 0
        for main_colum in header_content:
            if main_colum[1] == "":
                expense_worksheet.merge_range(
                    0, col, 1, col, main_colum[0], main_colum[3]
                )
            else:
                # Add sub columns in titles with 2 sub columns
                expense_worksheet.merge_range(
                    0, col, 0, col + 1, main_colum[0], main_colum[3]
                )
                expense_worksheet.write(1, col, main_colum[1], sub_format)
                expense_worksheet.write(1, col + 1, main_colum[2], sub_format)
                col += 1

            col += 1

        for line in range(2, 1002):
            expense_worksheet.write(
                line, 0, self.contract_code - 1, locked_cell_format
            )  # Column A
            expense_worksheet.write(line, 1, "", body_format)  # Column B
            expense_worksheet.write(line, 2, "", body_format)  # Column C
            expense_worksheet.write(line, 3, "", body_format)  # Column D
            expense_worksheet.write(line, 4, "", body_format)  # Column E
            expense_worksheet.write(line, 5, "", body_format)  # Column F

            # Column G
            expense_worksheet.write(line, 6, "", locked_cell_format)
            expense_worksheet.data_validation(
                line,
                6,
                self.contract_code,
                6,
                {
                    "validate": "list",
                    "source": "=nd_tab",
                    "input_message": "Escolha da lista",
                    "error_message": "Favor selecionar um dos itens listados ao clicar em  ▽  ao lado da célula",
                },
            )

            # Column H
            expense_worksheet.write(line, 7, "", locked_cell_format)
            expense_worksheet.data_validation(
                line,
                7,
                self.contract_code,
                7,
                {
                    "validate": "list",
                    "source": "=fv_tab",
                    "input_message": "Escolha da lista",
                    "error_message": "Favor selecionar um dos itens listados ao clicar em  ▽  ao lado da célula",
                },
            )

            # Column I com fórmula
            formula = (
                f'=IFERROR(VLOOKUP(J{self.contract_code+1},$FV.A$2:$FV.B$100,2),"")'
            )
            expense_worksheet.write(line, 8, formula, locked_cell_format)  # Column I

            # Column J
            expense_worksheet.write(line, 9, "", locked_cell_format)
            expense_worksheet.data_validation(
                line,
                9,
                self.contract_code,
                9,
                {
                    "validate": "list",
                    "source": "=ia_tab",
                    "input_message": "Escolha da lista",
                    "error_message": "Favor selecionar um dos itens listados ao clicar em  ▽  ao lado da célula",
                },
            )

            # Column K
            expense_worksheet.write(line, 10, "", locked_cell_format)
            expense_worksheet.data_validation(
                line,
                10,
                self.contract_code,
                10,
                {
                    "validate": "list",
                    "source": "=td_tab",
                    "input_message": "Escolha da lista",
                    "error_message": "Favor selecionar um dos itens listados ao clicar em  ▽  ao lado da célula",
                },
            )
            expense_worksheet.write(line, 11, "", body_format)  # Column L
            expense_worksheet.write(line, 12, "", body_format)  # Column M

        expense_worksheet.autofit()
        return expense_worksheet

    def __build_application_worksheet(self):
        application_worksheet = self.workbook.add_worksheet(
            name="3. APLICACOES E RESGATES"
        )
        header_format = self.workbook.add_format(
            {
                "bold": True,
                "border": 2,
                "align": "center",
                "valign": "vcenter",
                "fg_color": "#a3d7c6",
            }
        )
        header_breaking_line_format = self.workbook.add_format(
            {
                "bold": True,
                "border": 2,
                "align": "center",
                "valign": "vcenter",
                "fg_color": "#a3d7c6",
                "text_wrap": True,
            }
        )
        body_format = self.workbook.add_format(
            {
                "align": "center",
                "valign": "vcenter",
                "border": 1,
            }
        )
        locked_cell_format = self.workbook.add_format(
            {
                "align": "center",
                "valign": "vcenter",
                "border": 1,
                "bg_color": "#cfcdcd",
                "locked": True,
            }
        )
        header_content = (
            [" ID DO PROJETO ", header_breaking_line_format],
            [" VALOR ", header_format],
            [" DATA DA TRANSFERÊNCIA ", header_breaking_line_format],
            ["CONTA BANCÁRIA DE ORIGEM", header_breaking_line_format],
            ["FONTE DE RECURSO DE ORIGEM", header_breaking_line_format],
            ["CONTA BANCÁRIA", header_breaking_line_format],
            ["FONTE DE RECURSO DE DESTINO", header_breaking_line_format],
        )

        col = 0
        for main_colum in header_content:
            application_worksheet.merge_range(
                0, col, 1, col, main_colum[0], main_colum[1]
            )
            col += 1

        for line in range(2, 1002):
            application_worksheet.write(
                line, 0, self.contract_code, locked_cell_format
            )  # Column A
            application_worksheet.write(line, 1, "", body_format)  # Column B
            application_worksheet.write(line, 2, "", body_format)  # Column C

            # Column D
            application_worksheet.write(line, 3, "", locked_cell_format)
            application_worksheet.data_validation(
                line,
                3,
                self.contract_code,
                3,
                {
                    "validate": "list",
                    "source": "=cb_tab",
                    "input_message": "Escolha da lista",
                    "error_message": "Favor selecionar um dos itens listados ao clicar em  ▽  ao lado da célula",
                },
            )

            # Column E
            application_worksheet.write(line, 4, "", locked_cell_format)
            application_worksheet.data_validation(
                line,
                4,
                self.contract_code,
                4,
                {
                    "validate": "list",
                    "source": "=fr_tab",
                    "input_message": "Escolha da lista",
                    "error_message": "Favor selecionar um dos itens listados ao clicar em  ▽  ao lado da célula",
                },
            )

            # Column F
            application_worksheet.write(line, 5, "", locked_cell_format)
            application_worksheet.data_validation(
                line,
                5,
                self.contract_code,
                5,
                {
                    "validate": "list",
                    "source": "=cb_tab",
                    "input_message": "Escolha da lista",
                    "error_message": "Favor selecionar um dos itens listados ao clicar em  ▽  ao lado da célula",
                },
            )

            # Column G
            application_worksheet.write(line, 6, "", locked_cell_format)
            application_worksheet.data_validation(
                line,
                6,
                self.contract_code,
                6,
                {
                    "validate": "list",
                    "source": "=fr_tab",
                    "input_message": "Escolha da lista",
                    "error_message": "Favor selecionar um dos itens listados ao clicar em  ▽  ao lado da célula",
                },
            )

        application_worksheet.autofit()
        return application_worksheet

    def __build_revenue_worksheet(self):
        revenue_worksheet = self.workbook.add_worksheet(name="FR")

        body_format = self.workbook.add_format(
            {
                "align": "center",
                "valign": "vcenter",
                "border": 0,
                "bg_color": "#f0fc0a",
            }
        )
        revenue_worksheet.write(0, 0, "Nome", body_format)
        revenue_worksheet.write(0, 1, "ID", body_format)

        line = 1
        for source in self.organization.revenue_sources.all():
            revenue_worksheet.write(line, 0, source.name)
            revenue_worksheet.write(line, 1, str(source.id))
            line += 1

        revenue_worksheet.autofit()
        return revenue_worksheet

    def __build_bank_account_worksheet(self):
        bank_account_worksheet = self.workbook.add_worksheet(name="CB")
        body_format = self.workbook.add_format(
            {
                "align": "center",
                "valign": "vcenter",
                "border": 0,
                "bg_color": "#f0fc0a",
            }
        )

        bank_account_worksheet.write(0, 0, "Nome", body_format)
        bank_account_worksheet.write(0, 1, "ID", body_format)

        current_line = 1
        if self.contract.checking_account:
            bank_account_worksheet.write(
                current_line, 0, self.contract.checking_account.account
            )
            bank_account_worksheet.write(
                current_line, 1, str(self.contract.checking_account.id)
            )
            current_line += 1

        if self.contract.investing_account:
            bank_account_worksheet.write(
                current_line, 0, self.contract.investing_account.account
            )
            bank_account_worksheet.write(
                current_line, 1, str(self.contract.investing_account.id)
            )
            current_line += 1

        bank_account_worksheet.autofit()
        return bank_account_worksheet

    def __build_nature_category_worksheet(self):
        category_worksheet = self.workbook.add_worksheet(name="NR")
        body_format = self.workbook.add_format(
            {
                "align": "center",
                "valign": "vcenter",
                "border": 0,
                "bg_color": "#f0fc0a",
            }
        )
        category_worksheet.write(0, 0, "Nome", body_format)

        current_line = 1
        natures = [nature.label for nature in Revenue.Nature]
        for nature in natures:
            category_worksheet.write(current_line, 0, nature)
            current_line += 1

        category_worksheet.autofit()
        return category_worksheet

    def __build_expense_category_worksheet(self):
        expense_category_worksheet = self.workbook.add_worksheet(name="ND")
        body_format = self.workbook.add_format(
            {
                "align": "center",
                "valign": "vcenter",
                "border": 0,
                "bg_color": "#f0fc0a",
            }
        )
        expense_category_worksheet.write(0, 0, "Nome", body_format)

        current_line = 1
        natures = [nature.label for nature in NatureChoices]
        for nature in natures:
            expense_category_worksheet.write(current_line, 0, nature)
            current_line += 1

        expense_category_worksheet.autofit()
        return expense_category_worksheet

    def __build_favored_worksheet(self):
        favored_worksheet = self.workbook.add_worksheet(name="FV")
        body_format = self.workbook.add_format(
            {
                "align": "center",
                "valign": "vcenter",
                "border": 0,
                "bg_color": "#f0fc0a",
            }
        )
        favored_worksheet.write(0, 0, "Nome", body_format)
        favored_worksheet.write(0, 1, "ID", body_format)

        current_line = 1
        for favored in self.organization.favoreds.all():
            favored_worksheet.write(current_line, 0, favored.name)
            favored_worksheet.write(current_line, 1, str(favored.id))
            current_line += 1

        favored_worksheet.autofit()
        return favored_worksheet

    def __build_ia_worksheet(self):
        ia_worksheet = self.workbook.add_worksheet(name="IA")
        body_format = self.workbook.add_format(
            {
                "align": "center",
                "valign": "vcenter",
                "border": 0,
                "bg_color": "#f0fc0a",
            }
        )
        ia_worksheet.write(0, 0, "Nome", body_format)
        ia_worksheet.write(0, 1, "ID", body_format)

        current_line = 1
        for item in self.contract.items.all():
            ia_worksheet.write(current_line, 0, item.name)
            ia_worksheet.write(current_line, 1, str(item.id))
            current_line += 1

        ia_worksheet.autofit()
        return ia_worksheet

    def __build_doc_type_worksheet(self):
        doc_type_worksheet = self.workbook.add_worksheet(name="TD")
        body_format = self.workbook.add_format(
            {
                "align": "center",
                "valign": "vcenter",
                "border": 0,
                "bg_color": "#f0fc0a",
            }
        )

        doc_type_worksheet.write(0, 0, "Nome", body_format)

        current_line = 1
        documents = [document.label for document in Expense.DocumentChoices]
        for document in documents:
            doc_type_worksheet.write(current_line, 0, document)
            current_line += 1

        doc_type_worksheet.autofit()
        return doc_type_worksheet

    def __build_pr_worksheet(self):
        pr_worksheet = self.workbook.add_worksheet(name="PR")

        body_format = self.workbook.add_format(
            {
                "align": "center",
                "valign": "vcenter",
                "border": 0,
                "bg_color": "#f0fc0a",
            }
        )

        pr_worksheet.write(0, 0, "Nome", body_format)
        pr_worksheet.write(0, 1, "ID", body_format)

        # Preenchendo corpo (Inserir dados importados aqui)
        for id in range(1, 100):
            pr_worksheet.write(id, 0, "ID")
            pr_worksheet.write(id, 1, id)

        pr_worksheet.autofit()
        return pr_worksheet
