from datetime import datetime
from io import BytesIO

import xlsxwriter

from accountability.models import Accountability, Expense, Revenue
from accounts.models import Organization
from contracts.choices import NatureChoices
from contracts.models import Contract


class AccountabilityXLSXExporter:
    workbook: None

    def __init__(self, accountability: Accountability):
        self.contract: Contract = accountability.contract
        self.organization: Organization = accountability.contract.organization
        self.contract_code: int = accountability.contract.internal_code

    def handle(self):
        output = BytesIO()

        self.workbook: xlsxwriter.Workbook = xlsxwriter.Workbook(
            output, {"in_memory": True}
        )
        self.__build_formats()

        self._build_worksheets()
        self.workbook.define_name("fr_tab", "FR!$A$2:$A$5000")
        self.workbook.define_name("fd_tab", "FD!$A$2:$A$5000")
        self.workbook.define_name("cb_tab", "CB!$A$2:$A$5000")
        self.workbook.define_name("nr_tab", "NR!$A$2:$A$5000")
        self.workbook.define_name("nd_tab", "ND!$A$2:$A$5000")
        self.workbook.define_name("fv_tab", "FV!$A$2:$A$5000")
        self.workbook.define_name("ia_tab", "IA!$A$2:$A$5000")
        self.workbook.define_name("td_tab", "TD!$A$2:$A$5000")

        self.workbook.close()

        output.seek(0)
        return output

    def __build_formats(self):
        self.header_format = self.workbook.add_format(
            {
                "bold": True,
                "border": 2,
                "align": "center",
                "valign": "vcenter",
                "fg_color": "#a3d7c6",
            }
        )
        self.header_breaking_line_format = self.workbook.add_format(
            {
                "bold": True,
                "border": 2,
                "align": "center",
                "valign": "vcenter",
                "fg_color": "#a3d7c6",
                "text_wrap": True,
            }
        )
        self.body_format = self.workbook.add_format(
            {
                "align": "center",
                "valign": "vcenter",
                "border": 1,
            }
        )
        self.yellow_body_format = self.workbook.add_format(
            {
                "align": "center",
                "valign": "vcenter",
                "border": 0,
                "bg_color": "#f0fc0a",
            }
        )
        self.locked_cell_format = self.workbook.add_format(
            {
                "align": "center",
                "valign": "vcenter",
                "border": 1,
                "bg_color": "#cfcdcd",
                "locked": True,
            }
        )
        self.date_format = self.workbook.add_format(
            {
                "align": "center",
                "valign": "vcenter",
                "border": 1,
                "num_format": "dd/mm/yyyy",
            }
        )
        self.money_format = self.workbook.add_format(
            {
                "align": "center",
                "valign": "vcenter",
                "border": 1,
                "num_format": "R$ #,##0.00",
            }
        )

    def _build_worksheets(self):
        builders = [
            self.__build_receipt_worksheet,
            self.__build_expense_worksheet,
            self.__build_application_worksheet,
            self.__build_revenue_source_worksheet,
            self.__build_expense_source_worksheet,
            self.__build_bank_account_worksheet,
            self.__build_nature_category_worksheet,
            self.__build_expense_category_worksheet,
            self.__build_favored_worksheet,
            self.__build_ia_worksheet,
            self.__build_doc_type_worksheet,
        ]

        for builder in builders:
            builder()

    def __build_receipt_worksheet(self):
        receipt_worksheet = self.workbook.add_worksheet(name="1. RECEITAS")

        header_content = (
            [" Nº DA RECEITA ", self.header_format],
            [" CÓDIGO DO CONTRATO ", self.header_breaking_line_format],
            [" IDENTIFICAÇÃO ", self.header_format],
            [" VALOR ", self.header_format],
            [" RECEBIMENTO ", self.header_format],
            [" COMPETÊNCIA ", self.header_format],
            ["FONTE DE RECURSO", self.header_breaking_line_format],
            ["CONTA BANCÁRIA", self.header_breaking_line_format],
            ["NATUREZA DA RECEITA", self.header_breaking_line_format],
            [" OBSERVAÇÕES ", self.header_format],
        )

        col = 0
        for column_name, column_format in header_content:
            receipt_worksheet.merge_range(0, col, 1, col, column_name, column_format)
            col += 1

        for line in range(2, 1002):
            receipt_worksheet.write(line, 0, line - 1, self.locked_cell_format)
            receipt_worksheet.write(
                line, 1, self.contract_code, self.locked_cell_format
            )
            receipt_worksheet.write(line, 2, "", self.body_format)

            receipt_worksheet.write(line, 3, 0.00, self.money_format)
            receipt_worksheet.data_validation(
                line,
                3,
                line,
                3,
                options={
                    "validate": "decimal",
                    "criteria": "greater than or equal to",
                    "value": 0,
                    "input_message": "Digite um valor positivo em reais",
                    "error_message": "Por favor, insira um valor numérico válido (ex: 15,40)",
                    "error_type": "stop",
                },
            )

            receipt_worksheet.write(line, 4, "", self.date_format)
            receipt_worksheet.data_validation(
                line,
                4,
                line,
                4,
                options={
                    "validate": "date",
                    "criteria": "between",
                    "minimum": datetime(2020, 1, 1),
                    "maximum": datetime(2099, 12, 31),
                    "input_message": "Digite uma data no formato dd/mm/yyyy",
                    "error_message": "Por favor, insira uma data válida (dd/mm/yyyy)",
                    "error_type": "stop",
                },
            )

            receipt_worksheet.write(line, 5, "", self.date_format)
            receipt_worksheet.data_validation(
                line,
                5,
                line,
                5,
                options={
                    "validate": "date",
                    "criteria": "between",
                    "minimum": datetime(2020, 1, 1),
                    "maximum": datetime(2099, 12, 31),
                    "input_message": "Digite uma data no formato dd/mm/yyyy",
                    "error_message": "Por favor, insira uma data válida (dd/mm/yyyy)",
                    "error_type": "stop",
                },
            )

            receipt_worksheet.write(line, 6, "", self.locked_cell_format)
            receipt_worksheet.data_validation(
                line,
                6,
                line,
                6,
                options={
                    "validate": "list",
                    "source": "=fr_tab",
                    "input_message": "Escolha da lista",
                    "error_message": "Favor selecionar um dos itens listados ao clicar em  ▽  ao lado da célula",
                },
            )

            receipt_worksheet.write(line, 7, "", self.locked_cell_format)
            receipt_worksheet.data_validation(
                line,
                7,
                line,
                7,
                options={
                    "validate": "list",
                    "source": "=cb_tab",
                    "input_message": "Escolha da lista",
                    "error_message": "Favor selecionar um dos itens listados ao clicar em  ▽  ao lado da célula",
                },
            )

            receipt_worksheet.write(line, 8, "", self.locked_cell_format)
            receipt_worksheet.data_validation(
                line,
                8,
                line,
                8,
                options={
                    "validate": "list",
                    "source": "=nr_tab",
                    "input_message": "Escolha da lista",
                    "error_message": "Favor selecionar um dos itens listados ao clicar em  ▽  ao lado da célula",
                },
            )
            receipt_worksheet.write(line, 9, "", self.body_format)

        receipt_worksheet.autofit()
        return receipt_worksheet

    def __build_expense_worksheet(self):
        expense_worksheet = self.workbook.add_worksheet(name="2. DESPESAS")

        header_content = (
            [" Nº DA DESPESA ", self.header_format],
            [" CÓDIGO DO CONTRATO ", self.header_breaking_line_format],
            [" IDENTIFICAÇÃO ", self.header_format],
            [" VALOR ", self.header_format],
            [" VENCIMENTO ", self.header_format],
            [" COMPETÊNCIA ", self.header_format],
            [" FONTE DE RECURSO ", self.header_breaking_line_format],
            [
                " NATUREZA DA DESPESA (somente para despesa NÃO planejada)",
                self.header_breaking_line_format,
            ],
            [" FAVORECIDO/CONTRATADO", self.header_format],
            [
                "ITEM DE AQUISIÇÃO (somente despesa planejada)",
                self.header_breaking_line_format,
            ],
            [" TIPO DE DOCUMENTO", self.header_breaking_line_format],
            [" Nº DO DOCUMENTO ", self.header_format],
            [" OBSERVAÇÕES ", self.header_format],
        )

        col = 0
        for column_name, column_format in header_content:
            expense_worksheet.merge_range(
                0,
                col,
                1,
                col,
                column_name,
                column_format,
            )
            col += 1

        for line in range(2, 1002):
            expense_worksheet.write(line, 0, line - 1, self.locked_cell_format)
            expense_worksheet.write(
                line, 1, self.contract_code, self.locked_cell_format
            )
            expense_worksheet.write(line, 2, "", self.body_format)
            expense_worksheet.write(line, 3, 0.00, self.money_format)
            expense_worksheet.data_validation(
                line,
                3,
                line,
                3,
                options={
                    "validate": "decimal",
                    "criteria": "greater than or equal to",
                    "value": 0,
                    "input_message": "Digite um valor positivo em reais",
                    "error_message": "Por favor, insira um valor numérico válido (ex: 15,40)",
                    "error_type": "stop",
                },
            )

            expense_worksheet.write(line, 4, "", self.date_format)
            expense_worksheet.data_validation(
                line,
                4,
                line,
                4,
                options={
                    "validate": "date",
                    "criteria": "between",
                    "minimum": datetime(2020, 1, 1),
                    "maximum": datetime(2099, 12, 31),
                    "input_message": "Digite uma data no formato dd/mm/yyyy",
                    "error_message": "Por favor, insira uma data válida (dd/mm/yyyy)",
                    "error_type": "stop",
                },
            )

            expense_worksheet.write(line, 5, "", self.date_format)
            expense_worksheet.data_validation(
                line,
                5,
                line,
                5,
                options={
                    "validate": "date",
                    "criteria": "between",
                    "minimum": datetime(2020, 1, 1),
                    "maximum": datetime(2099, 12, 31),
                    "input_message": "Digite uma data no formato dd/mm/yyyy",
                    "error_message": "Por favor, insira uma data válida (dd/mm/yyyy)",
                    "error_type": "stop",
                },
            )

            expense_worksheet.write(line, 6, "", self.locked_cell_format)
            expense_worksheet.data_validation(
                line,
                6,
                line,
                6,
                options={
                    "validate": "list",
                    "source": "=fd_tab",
                    "input_message": "Escolha da lista",
                    "error_message": "Favor selecionar um dos itens listados ao clicar em  ▽  ao lado da célula",
                },
            )

            expense_worksheet.write(line, 7, "", self.locked_cell_format)
            expense_worksheet.data_validation(
                line,
                7,
                line,
                7,
                options={
                    "validate": "list",
                    "source": "=nd_tab",
                    "input_message": "Escolha da lista",
                    "error_message": "Favor selecionar um dos itens listados ao clicar em  ▽  ao lado da célula",
                },
            )

            expense_worksheet.write(line, 8, "", self.locked_cell_format)
            expense_worksheet.data_validation(
                line,
                8,
                line,
                8,
                options={
                    "validate": "list",
                    "source": "=fv_tab",
                    "input_message": "Escolha da lista",
                    "error_message": "Favor selecionar um dos itens listados ao clicar em  ▽  ao lado da célula",
                },
            )

            expense_worksheet.write(line, 9, "", self.locked_cell_format)
            expense_worksheet.data_validation(
                line,
                9,
                line,
                9,
                options={
                    "validate": "list",
                    "source": "=ia_tab",
                    "input_message": "Escolha da lista",
                    "error_message": "Favor selecionar um dos itens listados ao clicar em  ▽  ao lado da célula",
                },
            )

            expense_worksheet.write(line, 10, "", self.locked_cell_format)
            expense_worksheet.data_validation(
                line,
                10,
                line,
                10,
                options={
                    "validate": "list",
                    "source": "=td_tab",
                    "input_message": "Escolha da lista",
                    "error_message": "Favor selecionar um dos itens listados ao clicar em  ▽  ao lado da célula",
                },
            )
            expense_worksheet.write(line, 11, "", self.body_format)
            expense_worksheet.write(line, 12, "", self.body_format)

        expense_worksheet.autofit()
        return expense_worksheet

    def __build_application_worksheet(self):
        application_worksheet = self.workbook.add_worksheet(
            name="3. APLICACOES E RESGATES"
        )
        header_content = (
            [" Nº DA APLICAÇÃO ", self.header_format],
            [" CÓDIGO DO CONTRATO ", self.header_breaking_line_format],
            [" VALOR ", self.header_format],
            [" DATA DA TRANSFERÊNCIA ", self.header_breaking_line_format],
            [" Nº DOCUMENTO ", self.header_breaking_line_format],
            ["CONTA BANCÁRIA DE ORIGEM", self.header_breaking_line_format],
            ["CONTA BANCÁRIA DE DESTINO", self.header_breaking_line_format],
        )

        col = 0
        for column_name, column_format in header_content:
            application_worksheet.merge_range(
                0, col, 1, col, column_name, column_format
            )
            col += 1

        for line in range(2, 1002):
            application_worksheet.write(line, 0, line - 1, self.locked_cell_format)
            application_worksheet.write(
                line, 1, self.contract_code, self.locked_cell_format
            )
            application_worksheet.write(line, 2, 0.00, self.money_format)
            application_worksheet.data_validation(
                line,
                2,
                line,
                2,
                options={
                    "validate": "decimal",
                    "criteria": "greater than or equal to",
                    "value": 0,
                    "input_message": "Digite um valor positivo em reais",
                    "error_message": "Por favor, insira um valor numérico válido (ex: 15,40)",
                    "error_type": "stop",
                },
            )

            application_worksheet.write(line, 3, "", self.date_format)
            application_worksheet.data_validation(
                line,
                3,
                line,
                3,
                options={
                    "validate": "date",
                    "criteria": "between",
                    "minimum": datetime(2020, 1, 1),
                    "maximum": datetime(2099, 12, 31),
                    "input_message": "Digite uma data no formato dd/mm/yyyy",
                    "error_message": "Por favor, insira uma data válida (dd/mm/yyyy)",
                    "error_type": "stop",
                },
            )

            application_worksheet.write(line, 4, "", self.body_format)

            application_worksheet.write(line, 5, "", self.locked_cell_format)
            application_worksheet.data_validation(
                line,
                5,
                line,
                5,
                options={
                    "validate": "list",
                    "source": "=cb_tab",
                    "input_message": "Escolha da lista",
                    "error_message": "Favor selecionar um dos itens listados ao clicar em  ▽  ao lado da célula",
                },
            )

            application_worksheet.write(line, 6, "", self.locked_cell_format)
            application_worksheet.data_validation(
                line,
                6,
                line,
                6,
                options={
                    "validate": "list",
                    "source": "=cb_tab",
                    "input_message": "Escolha da lista",
                    "error_message": "Favor selecionar um dos itens listados ao clicar em  ▽  ao lado da célula",
                },
            )

        application_worksheet.autofit()
        return application_worksheet

    def __build_expense_source_worksheet(self):
        revenue_worksheet = self.workbook.add_worksheet(name="FD")
        revenue_worksheet.write(0, 0, "Nome", self.yellow_body_format)
        revenue_worksheet.write(0, 1, "ID", self.yellow_body_format)

        line = 1
        for source in self.organization.resource_sources.all():
            revenue_worksheet.write(line, 0, source.name)
            revenue_worksheet.write(line, 1, str(source.id))
            line += 1

        revenue_worksheet.autofit()
        return revenue_worksheet

    def __build_revenue_source_worksheet(self):
        rev_source_worksheet = self.workbook.add_worksheet(name="FR")
        rev_source_worksheet.write(0, 0, "Nome", self.yellow_body_format)

        current_line = 1
        sources = [source.label for source in Revenue.RevenueSource]
        for source in sources:
            rev_source_worksheet.write(current_line, 0, source)
            current_line += 1

        rev_source_worksheet.autofit()
        return rev_source_worksheet

    def __build_bank_account_worksheet(self):
        bank_account_worksheet = self.workbook.add_worksheet(name="CB")
        bank_account_worksheet.write(0, 0, "Nome", self.yellow_body_format)
        bank_account_worksheet.write(0, 1, "ID", self.yellow_body_format)

        current_line = 1
        if self.contract.checking_account:
            bank_account_worksheet.write(
                current_line,
                0,
                "CONTA CORRENTE",
                self.locked_cell_format,
            )
            bank_account_worksheet.write(
                current_line,
                1,
                str(self.contract.checking_account.id),
                self.locked_cell_format,
            )
            current_line += 1

        if self.contract.investing_account:
            bank_account_worksheet.write(
                current_line,
                0,
                "CONTA INVESTIMENTO",
                self.locked_cell_format,
            )
            bank_account_worksheet.write(
                current_line,
                1,
                str(self.contract.investing_account.id),
                self.locked_cell_format,
            )
            current_line += 1

        bank_account_worksheet.autofit()
        return bank_account_worksheet

    def __build_nature_category_worksheet(self):
        category_worksheet = self.workbook.add_worksheet(name="NR")
        category_worksheet.write(0, 0, "Nome", self.yellow_body_format)

        current_line = 1
        natures = [nature.label for nature in Revenue.Nature]
        for nature in natures:
            category_worksheet.write(current_line, 0, nature)
            current_line += 1

        category_worksheet.autofit()
        return category_worksheet

    def __build_expense_category_worksheet(self):
        expense_category_worksheet = self.workbook.add_worksheet(name="ND")
        expense_category_worksheet.write(0, 0, "Nome", self.yellow_body_format)

        current_line = 1
        natures = [nature.label for nature in NatureChoices]
        for nature in natures:
            expense_category_worksheet.write(current_line, 0, nature)
            current_line += 1

        expense_category_worksheet.autofit()
        return expense_category_worksheet

    def __build_favored_worksheet(self):
        favored_worksheet = self.workbook.add_worksheet(name="FV")
        favored_worksheet.write(0, 0, "Nome", self.yellow_body_format)
        favored_worksheet.write(0, 1, "Documento", self.yellow_body_format)

        current_line = 1
        for favored in self.organization.favoreds.all():
            favored_worksheet.write(current_line, 0, favored.name)
            favored_worksheet.write(current_line, 1, str(favored.document))
            current_line += 1

        favored_worksheet.autofit()
        return favored_worksheet

    def __build_ia_worksheet(self):
        ia_worksheet = self.workbook.add_worksheet(name="IA")
        ia_worksheet.write(0, 0, "Nome", self.yellow_body_format)
        ia_worksheet.write(0, 1, "ID", self.yellow_body_format)

        current_line = 1
        for item in self.contract.items.all():
            ia_worksheet.write(current_line, 0, item.name)
            ia_worksheet.write(current_line, 1, str(item.id))
            current_line += 1

        ia_worksheet.autofit()
        return ia_worksheet

    def __build_doc_type_worksheet(self):
        doc_type_worksheet = self.workbook.add_worksheet(name="TD")
        doc_type_worksheet.write(0, 0, "Nome", self.yellow_body_format)

        current_line = 1
        documents = [document.label for document in Expense.DocumentChoices]
        for document in documents:
            doc_type_worksheet.write(current_line, 0, document)
            current_line += 1

        doc_type_worksheet.autofit()
        return doc_type_worksheet
