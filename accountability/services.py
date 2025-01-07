from datetime import datetime

import xlsxwriter


class AccountabilityCSVExporter:
    workbook: None

    def handle(self):
        # Criar modelo de Fornecedor

        archive = f"archive-{str(datetime.now().time())[0:8]}.xlsx"

        # Cria planilha e abas.
        self.workbook = xlsxwriter.Workbook(archive)
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

        return self.workbook

    def _build_worksheets(self):
        builders = [
            self.__build_receipt_worksheet,
            self.__build_expense_worksheet,
            self.__build_application_worksheet,
            self.__build_resource_source_worksheet,
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

        # Formatação células corpo (linha 3)
        body_format = self.workbook.add_format(
            {
                "align": "center",
                "valign": "vcenter",
                "border": 1,
                # "fg_color": "#efe920",
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

        # Criando cabeçalho
        header_content = (
            [" ID DO PROJETO ", header_breaking_line_format],
            [" IDENTIFICAÇÃO ", header_format],
            [" VALOR ", header_format],
            [" VENCIMENTO ", header_format],
            [" COMPETÊNCIA ", header_format],
            ["FONTE DE RECURSO", header_breaking_line_format],
            ["CONTA BANCÁRIA", header_breaking_line_format],
            ["NATUREZA DA RECEITA", header_breaking_line_format],
            [" OBSERVAÇÕES ", header_format],
        )

        # Preenchendo cabeçalho

        col = 0
        for main_colum in header_content:
            receipt_worksheet.merge_range(0, col, 1, col, main_colum[0], main_colum[1])

            col += 1

        # Preenchendo corpo
        for id in range(2, 1002):
            # Inserir variável de alteração do "ID DO PROJETO" no segundo zero da Coluna A
            receipt_worksheet.write(id, 0, id - 1, locked_cell_format)  # Coluna A
            receipt_worksheet.write(id, 1, "", body_format)  # Coluna B
            receipt_worksheet.write(id, 2, "", body_format)  # Coluna C
            receipt_worksheet.write(id, 3, "", body_format)  # Coluna D
            receipt_worksheet.write(id, 4, "", body_format)  # Coluna E

            # Coluna F
            receipt_worksheet.write(id, 5, "", locked_cell_format)
            receipt_worksheet.data_validation(
                id,
                5,
                id,
                5,
                {
                    "validate": "list",
                    "source": "=fr_tab",
                    "input_message": "Escolha da lista",
                    "error_message": "Favor selecionar um dos itens listados ao clicar em  ▽   ao lado da célula",
                },
            )

            # Coluna G
            receipt_worksheet.write(id, 6, "", locked_cell_format)
            receipt_worksheet.data_validation(
                id,
                6,
                id,
                6,
                {
                    "validate": "list",
                    "source": "=cb_tab",
                    "input_message": "Escolha da lista",
                    "error_message": "Favor selecionar um dos itens listados ao clicar em  ▽  ao lado da célula",
                },
            )

            # Coluna H
            receipt_worksheet.write(id, 7, "", locked_cell_format)
            receipt_worksheet.data_validation(
                id,
                7,
                id,
                7,
                {
                    "validate": "list",
                    "source": "=nr_tab",
                    "input_message": "Escolha da lista",
                    "error_message": "Favor selecionar um dos itens listados ao clicar em  ▽  ao lado da célula",
                },
            )
            receipt_worksheet.write(id, 8, "", body_format)  # Coluna I

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

        # Formatação células sub título (linha 2)
        sub_format = self.workbook.add_format(
            {
                "align": "center",
                "valign": "vcenter",
                "fg_color": "#efe920",
                "border": 2,
                "text_wrap": True,
            }
        )

        # Formatação células corpo (linha 3)
        body_format = self.workbook.add_format(
            {
                "align": "center",
                "valign": "vcenter",
                "border": 1,
                # "fg_color": "#efe920",
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

        # Criando cabeçalho
        header_content = (
            [" ID DO PROJETO ", "", "", header_breaking_line_format],
            [" IDENTIFICAÇÃO ", "", "", header_format],
            [" VALOR ", "", "", header_format],
            [" VENCIMENTO ", "", "", header_format],
            [" COMPETÊNCIA ", "", "", header_format],
            ["FONTE DE RECURSO", "", "", header_breaking_line_format],
            [
                "NATUREZA DA DESPESA (somente para despesa NÃO planejada)",
                "",
                "",
                header_breaking_line_format,
            ],
            ["FAVORECIDO/CONTRATADO", "Nome", "CPF/CNPJ", header_format],
            [
                "ITEM DE AQUISIÇÃO (somente despesa planejada)",
                "",
                "",
                header_breaking_line_format,
            ],
            [" TIṔO DE DOCUMENTO", "", "", header_breaking_line_format],
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
                # Adiciona sub colunas em Títulos com 2 sub colunas
                expense_worksheet.merge_range(
                    0, col, 0, col + 1, main_colum[0], main_colum[3]
                )
                expense_worksheet.write(1, col, main_colum[1], sub_format)
                expense_worksheet.write(1, col + 1, main_colum[2], sub_format)
                col += 1

            col += 1

        for id in range(2, 1002):
            # Inserir variável de alteração do "ID DO PROJETO" no segundo zero da Coluna A
            expense_worksheet.write(id, 0, id - 1, locked_cell_format)  # Coluna A
            expense_worksheet.write(id, 1, "", body_format)  # Coluna B
            expense_worksheet.write(id, 2, "", body_format)  # Coluna C
            expense_worksheet.write(id, 3, "", body_format)  # Coluna D
            expense_worksheet.write(id, 4, "", body_format)  # Coluna E
            expense_worksheet.write(id, 5, "", body_format)  # Coluna F

            # Coluna G
            expense_worksheet.write(id, 6, "", locked_cell_format)
            expense_worksheet.data_validation(
                id,
                6,
                id,
                6,
                {
                    "validate": "list",
                    "source": "=nd_tab",
                    "input_message": "Escolha da lista",
                    "error_message": "Favor selecionar um dos itens listados ao clicar em  ▽  ao lado da célula",
                },
            )

            # Coluna H
            expense_worksheet.write(id, 7, "", locked_cell_format)
            expense_worksheet.data_validation(
                id,
                7,
                id,
                7,
                {
                    "validate": "list",
                    "source": "=fv_tab",
                    "input_message": "Escolha da lista",
                    "error_message": "Favor selecionar um dos itens listados ao clicar em  ▽  ao lado da célula",
                },
            )

            # Coluna I com fórmula
            formula = f'=IFERROR(VLOOKUP(J{id+1},$FV.A$2:$FV.B$100,2),"")'
            expense_worksheet.write(id, 8, formula, locked_cell_format)  # Coluna I

            # Coluna J
            expense_worksheet.write(id, 9, "", locked_cell_format)
            expense_worksheet.data_validation(
                id,
                9,
                id,
                9,
                {
                    "validate": "list",
                    "source": "=ia_tab",
                    "input_message": "Escolha da lista",
                    "error_message": "Favor selecionar um dos itens listados ao clicar em  ▽  ao lado da célula",
                },
            )

            # Coluna K
            expense_worksheet.write(id, 10, "", locked_cell_format)
            expense_worksheet.data_validation(
                id,
                10,
                id,
                10,
                {
                    "validate": "list",
                    "source": "=td_tab",
                    "input_message": "Escolha da lista",
                    "error_message": "Favor selecionar um dos itens listados ao clicar em  ▽  ao lado da célula",
                },
            )
            expense_worksheet.write(id, 11, "", body_format)  # Coluna L
            expense_worksheet.write(id, 12, "", body_format)  # Coluna M

        expense_worksheet.autofit()
        return expense_worksheet

    def __build_application_worksheet(self):
        application_worksheet = self.workbook.add_worksheet(
            name="3. APLICACOES E RESGATES"
        )

        # Formatação células cabeçalho (linha 1)
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

        # Formatação células corpo (linha 3)
        body_format = self.workbook.add_format(
            {
                "align": "center",
                "valign": "vcenter",
                "border": 1,
                # "fg_color": "#efe920",
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

        # Criando cabeçalho
        header_content = (
            [" ID DO PROJETO ", header_breaking_line_format],
            [" VALOR ", header_format],
            [" DATA DA TRANSFERÊNCIA ", header_breaking_line_format],
            ["CONTA BANCÁRIA DE ORIGEM", header_breaking_line_format],
            ["FONTE DE RECURSO DE ORIGEM", header_breaking_line_format],
            ["CONTA BANCÁRIA", header_breaking_line_format],
            ["FONTE DE RECURSO DE DESTINO", header_breaking_line_format],
        )

        # Preenchendo cabeçalho
        col = 0
        for main_colum in header_content:
            application_worksheet.merge_range(
                0, col, 1, col, main_colum[0], main_colum[1]
            )

            col += 1

        # Preenchendo corpo
        for id in range(2, 1002):
            # Inserir variável de alteração do "ID DO PROJETO" no segundo zero da Coluna A
            application_worksheet.write(id, 0, id - 1, locked_cell_format)  # Coluna A
            application_worksheet.write(id, 1, "", body_format)  # Coluna B
            application_worksheet.write(id, 2, "", body_format)  # Coluna C

            # Coluna D
            application_worksheet.write(id, 3, "", locked_cell_format)
            application_worksheet.data_validation(
                id,
                3,
                id,
                3,
                {
                    "validate": "list",
                    "source": "=cb_tab",
                    "input_message": "Escolha da lista",
                    "error_message": "Favor selecionar um dos itens listados ao clicar em  ▽  ao lado da célula",
                },
            )

            # Coluna E
            application_worksheet.write(id, 4, "", locked_cell_format)
            application_worksheet.data_validation(
                id,
                4,
                id,
                4,
                {
                    "validate": "list",
                    "source": "=fr_tab",
                    "input_message": "Escolha da lista",
                    "error_message": "Favor selecionar um dos itens listados ao clicar em  ▽  ao lado da célula",
                },
            )

            # Coluna F
            application_worksheet.write(id, 5, "", locked_cell_format)
            application_worksheet.data_validation(
                id,
                5,
                id,
                5,
                {
                    "validate": "list",
                    "source": "=cb_tab",
                    "input_message": "Escolha da lista",
                    "error_message": "Favor selecionar um dos itens listados ao clicar em  ▽  ao lado da célula",
                },
            )

            # Coluna G
            application_worksheet.write(id, 6, "", locked_cell_format)
            application_worksheet.data_validation(
                id,
                6,
                id,
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

    def __build_resource_source_worksheet(self):
        resource_source_worksheet = self.workbook.add_worksheet(name="FR")

        body_format = self.workbook.add_format(
            {
                "align": "center",
                "valign": "vcenter",
                "border": 0,
                "bg_color": "#f0fc0a",
            }
        )

        # Cabeçalho
        resource_source_worksheet.write(0, 0, "NOME", body_format)
        resource_source_worksheet.write(0, 1, "ID", body_format)

        # Preenchendo corpo (Inserir dados importados aqui)
        for id in range(1, 100):
            resource_source_worksheet.write(id, 0, "ID")
            resource_source_worksheet.write(id, 1, id)

        resource_source_worksheet.autofit()
        return resource_source_worksheet

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

        # Cabeçalho
        bank_account_worksheet.write(0, 0, "NOME", body_format)
        bank_account_worksheet.write(0, 1, "ID", body_format)

        # Preenchendo corpo (Inserir dados importados aqui)
        for id in range(1, 100):
            bank_account_worksheet.write(id, 0, "ID")
            bank_account_worksheet.write(id, 1, id)

        bank_account_worksheet.autofit()
        return bank_account_worksheet

    def __build_category_worksheet(self):
        category_worksheet = self.workbook.add_worksheet(name="NR")

        body_format = self.workbook.add_format(
            {
                "align": "center",
                "valign": "vcenter",
                "border": 0,
                "bg_color": "#f0fc0a",
            }
        )

        # Cabeçalho
        category_worksheet.write(0, 0, "NOME", body_format)
        category_worksheet.write(0, 1, "ID", body_format)

        # Preenchendo corpo (Inserir dados importados aqui)
        for id in range(1, 100):
            category_worksheet.write(id, 0, "ID")
            category_worksheet.write(id, 1, id)

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

        # Cabeçalho
        expense_category_worksheet.write(0, 0, "NOME", body_format)
        expense_category_worksheet.write(0, 1, "ID", body_format)

        # Preenchendo corpo (Inserir dados importados aqui)
        for id in range(1, 100):
            expense_category_worksheet.write(id, 0, "ID")
            expense_category_worksheet.write(id, 1, id)

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

        # Cabeçalho
        favored_worksheet.write(0, 0, "NOME", body_format)
        favored_worksheet.write(0, 1, "ID", body_format)

        # Preenchendo corpo (Inserir dados importados aqui)
        for id in range(1, 100):
            favored_worksheet.write(id, 0, "ID")
            favored_worksheet.write(id, 1, id)

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

        # Cabeçalho
        ia_worksheet.write(0, 0, "NOME", body_format)
        ia_worksheet.write(0, 1, "ID", body_format)

        # Preenchendo corpo (Inserir dados importados aqui)
        for id in range(1, 100):
            ia_worksheet.write(id, 0, "ID")
            ia_worksheet.write(id, 1, id)

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

        # Cabeçalho
        doc_type_worksheet.write(0, 0, "NOME", body_format)
        doc_type_worksheet.write(0, 1, "ID", body_format)

        # Preenchendo corpo (Inserir dados importados aqui)
        for id in range(1, 100):
            doc_type_worksheet.write(id, 0, "ID")
            doc_type_worksheet.write(id, 1, id)

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

        # Cabeçalho
        pr_worksheet.write(0, 0, "NOME", body_format)
        pr_worksheet.write(0, 1, "ID", body_format)

        # Preenchendo corpo (Inserir dados importados aqui)
        for id in range(1, 100):
            pr_worksheet.write(id, 0, "ID")
            pr_worksheet.write(id, 1, id)

        pr_worksheet.autofit()
        return pr_worksheet

        # formula = (
        #    f'=IFERROR(VLOOKUP(F{id+1},$FR.A$2:$FR.B$100,2),"")'  # fórmula coluna G
        # )


if __name__ == "__main__":
    AccountabilityCSVExporter().handle()
