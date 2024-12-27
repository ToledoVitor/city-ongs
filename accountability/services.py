import xlsxwriter
from datetime import datetime


class AccountabilityCSVExporter:
    workbook: None

    def handle(self):
        # Criar modelo de Fornecedor

        archive = f"archive-{str(datetime.now().time())[0:8]}.xlsx"

        # Cria planilha e abas.
        self.workbook = xlsxwriter.Workbook(archive)
        self._build_worksheets()
        self.workbook.close()

        return self.workbook

    def _build_worksheets(self):
        builders = [
            self.__build_receipt_worksheet,
            self.__build_expense_worksheet,
            self.__build_application_worksheet,
            self.__build_fr_worksheet,
            self.__build_bank_account_worksheet,
            self.__build_category_worksheet,
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

        # Formatação células cabeçalho (linha 1)
        header_format = self.workbook.add_format(
            {
                "bold": True,
                # 'border':   6,
                "align": "center",
                "valign": "vcenter",
                "fg_color": "#a3d7c6",
            }
        )

        # Formatação células sub título (linha 2)
        sub_format = self.workbook.add_format(
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
                receipt_worksheet.merge_range(
                    0, col, 0, col + 1, main_colum, header_format
                )
                receipt_worksheet.write(1, col, sub1, sub_format)
                receipt_worksheet.write(1, col + 1, sub2, sub_format)
                col += 1

            col += 1

        receipt_worksheet.autofit()
        return receipt_worksheet

    def __build_expense_worksheet(self):
        content = [""]

        expense_worksheet = self.workbook.add_worksheet(name="2. DESPESAS")
        # PREENCHER AQUI

        return expense_worksheet

    def __build_application_worksheet(self):
        content = [""]

        application_worksheet = self.workbook.add_worksheet(
            name="3. APLICACOES E RESGATES"
        )
        # PREENCHER AQUI

        return application_worksheet

    def __build_fr_worksheet(self):
        content = [""]

        fr_worksheet = self.workbook.add_worksheet(name="FR")
        # PREENCHER AQUI

        return fr_worksheet

    def __build_bank_account_worksheet(self):
        content = [""]

        bank_account_worksheet = self.workbook.add_worksheet(name="CB")
        # PREENCHER AQUI

        return bank_account_worksheet

    def __build_category_worksheet(self):
        content = [""]

        category_worksheet = self.workbook.add_worksheet(name="NR")
        # PREENCHER AQUI

        return category_worksheet

    def __build_expense_category_worksheet(self):
        content = [""]

        expense_category_worksheet = self.workbook.add_worksheet(name="ND")
        # PREENCHER AQUI

        return expense_category_worksheet

    def __build_favored_worksheet(self):
        content = [""]

        favored_worksheet = self.workbook.add_worksheet(name="FV")
        # PREENCHER AQUI

        return favored_worksheet

    def __build_ia_worksheet(self):
        content = [""]

        ia_worksheet = self.workbook.add_worksheet(name="IA")
        # PREENCHER AQUI

        return ia_worksheet

    def __build_doc_type_worksheet(self):
        content = [""]

        doc_type_worksheet = self.workbook.add_worksheet(name="TD")
        # PREENCHER AQUI

        return doc_type_worksheet

    def __build_pr_worksheet(self):
        content = [""]

        pr_worksheet = self.workbook.add_worksheet(name="PR")
        # PREENCHER AQUI

        return pr_worksheet


if __name__ == "__main__":
    AccountabilityCSVExporter().handle()
