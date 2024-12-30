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
                "locked": False,
            }
        )

        # Criando cabeçalho
        header_content = (
            [" ID DO PROJETO ", "", ""],
            [" IDENTIFICAÇÃO ", "", ""],
            [" VALOR ", "", ""],
            [" VENCIMENTO ", "", ""],
            [" COMPETÊNCIA ", "", ""],
            ["FONTE DE RECURSO", "Nome", "ID (não preencher)"],
            ["CONTA BANCÁRIA", "Nome", "ID (não preencher)"],
            ["NATUREZA DA RECEITA", "Nome", "ID (não preencher)"],
            [" OBSERVAÇÕES ", "", ""],
        )

        # Preenchendo cabeçalho

        col = 0
        for main_colum, sub1, sub2 in header_content:
            if col == 0:
                receipt_worksheet.merge_range(
                    0, 0, 1, 0, main_colum, header_breaking_line_format
                )
            elif sub1 == "":
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

        # Preenchendo corpo
        for id in range(2, 1002):
            # Inserir variável de alteração do "ID DO PROJETO" no segundo zero da Coluna A
            receipt_worksheet.write(id, 0, id - 1, body_format)  # Coluna A
            receipt_worksheet.write(id, 1, "", body_format)  # Coluna B
            receipt_worksheet.write(id, 2, "", body_format)  # Coluna C
            receipt_worksheet.write(id, 3, "", body_format)  # Coluna D
            receipt_worksheet.write(id, 4, "", body_format)  # Coluna E
            receipt_worksheet.write(id, 5, "", body_format)  # Coluna F
            formula = (
                f'=IFERROR(VLOOKUP(F{id+1},$FR.A$2:$FR.B$100,2),"")'  # fórmula coluna G
            )
            receipt_worksheet.write(id, 6, formula, locked_cell_format)  # Coluna G
            receipt_worksheet.write(id, 7, "", body_format)  # Coluna H
            formula = (
                f'=IFERROR(VLOOKUP(H{id+1},$CB.A$2:$CB.B$100,2),"")'  # fórmula coluna I
            )
            receipt_worksheet.write(id, 8, formula, locked_cell_format)  # Coluna I
            receipt_worksheet.write(id, 9, "", body_format)  # Coluna J
            formula = (
                f'=IFERROR(VLOOKUP(J{id+1},$NR.A$2:$CB.B$100,2),"")'  # fórmula coluna K
            )
            receipt_worksheet.write(id, 10, formula, locked_cell_format)  # Coluna K
            receipt_worksheet.write(id, 11, "", body_format)  # Coluna L

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
                "locked": False,
            }
        )

        # Criando cabeçalho
        header_content = (
            [" ID DO PROJETO ", "", "", ""],
            [" IDENTIFICAÇÃO ", "", "", ""],
            [" VALOR ", "", "", ""],
            [" VENCIMENTO ", "", "", ""],
            [" COMPETÊNCIA ", "", "", ""],
            ["FONTE DE RECURSO", "Nome", "ID (não preencher)", ""],
            [
                "NATUREZA DA DESPESA (somente para despesa NÃO planejada)",
                "Nome",
                "ID (não preencher)",
                "",
            ],
            ["FAVORECIDO/CONTRATADO", "Nome", "CPF/CNPJ", "ID (não preencher)"],
            [
                "ITEM DE AQUISIÇÃO (somente despesa planejada)",
                "Especifição",
                "ID (não preencher)",
                "",
            ],
            [" TIṔO DE DOCUMENTO", "Nome", "ID (não preencher)", ""],
            [" Nº DO DOCUMENTO ", "", "", ""],
            [" OBSERVAÇÕES ", "", "", ""],
        )

        col = 0
        for main_colum, sub1, sub2, sub3 in header_content:
            if col == 0:
                expense_worksheet.merge_range(
                    0, 0, 1, 0, main_colum, header_breaking_line_format
                )
            elif sub1 == "":
                # Adiciona texto e mesclas células 1 e 2 de suas respectivas colunas
                expense_worksheet.merge_range(0, col, 1, col, main_colum, header_format)

            elif sub3 == "":
                # Adiciona sub colunas em Títulos com 2 sub colunas
                expense_worksheet.merge_range(
                    0, col, 0, col + 1, main_colum, header_format
                )
                expense_worksheet.write(1, col, sub1, sub_format)
                expense_worksheet.write(1, col + 1, sub2, sub_format)
                col += 1
            else:
                # Adiciona sub colunas em Títulos com 2 sub colunas
                expense_worksheet.merge_range(
                    0, col, 0, col + 2, main_colum, header_format
                )
                expense_worksheet.write(1, col, sub1, sub_format)
                expense_worksheet.write(1, col + 1, sub2, sub_format)
                expense_worksheet.write(1, col + 2, sub3, sub_format)
                col += 2

            col += 1

        for id in range(2, 1002):
            # Inserir variável de alteração do "ID DO PROJETO" no segundo zero da Coluna A
            expense_worksheet.write(id, 0, id - 1, body_format)  # Coluna A
            expense_worksheet.write(id, 1, "", body_format)  # Coluna B
            expense_worksheet.write(id, 2, "", body_format)  # Coluna C
            expense_worksheet.write(id, 3, "", body_format)  # Coluna D
            expense_worksheet.write(id, 4, "", body_format)  # Coluna E
            expense_worksheet.write(id, 5, "", body_format)  # Coluna F
            formula = (
                f'=IFERROR(VLOOKUP(F{id+1},$FR.A$2:$FR.B$100,2),"")'  # fórmula coluna G
            )
            expense_worksheet.write(id, 6, formula, locked_cell_format)  # Coluna G
            expense_worksheet.write(id, 7, "", body_format)  # Coluna H
            formula = (
                f'=IFERROR(VLOOKUP(H{id+1},$ND.A$2:$ND.B$100,2),"")'  # fórmula coluna I
            )
            expense_worksheet.write(id, 8, formula, locked_cell_format)  # Coluna I
            expense_worksheet.write(id, 9, "", body_format)  # Coluna J
            formula = (
                f'=IFERROR(VLOOKUP(J{id+1},$FV.A$2:$FV.B$100,2),"")'  # fórmula coluna K
            )
            expense_worksheet.write(id, 10, formula, locked_cell_format)  # Coluna K
            formula = (
                f'=IFERROR(VLOOKUP(J{id+1},$FV.A$2:$FV.B$100,3),"")'  # fórmula coluna L
            )
            expense_worksheet.write(id, 11, formula, locked_cell_format)  # Coluna L
            expense_worksheet.write(id, 12, "", body_format)  # Coluna M
            formula = (
                f'=IFERROR(VLOOKUP(M{id+1},$IA.A$2:$IA.B$100,2),"")'  # fórmula coluna N
            )
            expense_worksheet.write(id, 13, formula, locked_cell_format)  # Coluna N
            expense_worksheet.write(id, 14, "", body_format)  # Coluna O
            formula = (
                f'=IFERROR(VLOOKUP(M{id+1},$IA.A$2:$IA.B$100,2),"")'  # fórmula coluna P
            )
            expense_worksheet.write(id, 15, formula, locked_cell_format)  # Coluna P
            expense_worksheet.write(id, 16, "", body_format)  # Coluna Q
            expense_worksheet.write(id, 17, "", body_format)  # Coluna R

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
                "locked": False,
            }
        )

        # Criando cabeçalho
        header_content = (
            [" ID DO PROJETO ", "", ""],
            [" VALOR ", "", ""],
            [" DATA DA TRANSFERÊNCIA ", "", ""],
            ["CONTA BANCÁRIA DE ORIGEM", "Nome", "ID (não preencher)"],
            ["FONTE DE RECURSO DE ORIGEM", "Nome", "ID (não preencher)"],
            ["CONTA BANCÁRIA", "Nome", "ID (não preencher)"],
            ["FONTE DE RECURSO DE DESTINO", "Nome", "ID (não preencher)"],
        )

        # Preenchendo cabeçalho

        col = 0
        for main_colum, sub1, sub2 in header_content:
            if col == 0:
                application_worksheet.merge_range(
                    0, 0, 1, 0, main_colum, header_breaking_line_format
                )
            elif sub1 == "":
                # Adiciona texto e mesclas células 1 e 2 de suas respectivas colunas
                application_worksheet.merge_range(
                    0, col, 1, col, main_colum, header_format
                )

            else:
                # Adiciona sub coluna mescla colunas de acordo com o seu título
                application_worksheet.merge_range(
                    0, col, 0, col + 1, main_colum, header_format
                )
                application_worksheet.write(1, col, sub1, sub_format)
                application_worksheet.write(1, col + 1, sub2, sub_format)
                col += 1

            col += 1

        # Preenchendo corpo
        for id in range(2, 1002):
            # Inserir variável de alteração do "ID DO PROJETO" no segundo zero da Coluna A
            application_worksheet.write(id, 0, id - 1, body_format)  # Coluna A
            application_worksheet.write(id, 1, "", body_format)  # Coluna B
            application_worksheet.write(id, 2, "", body_format)  # Coluna C
            application_worksheet.write(id, 3, "", body_format)  # Coluna D
            formula = (
                f'=IFERROR(VLOOKUP(D{id+1},$CB.A$2:$CB.B$100,2),"")'  # fórmula coluna E
            )
            application_worksheet.write(id, 4, formula, locked_cell_format)  # Coluna E
            application_worksheet.write(id, 5, "", body_format)  # Coluna F
            formula = (
                f'=IFERROR(VLOOKUP(F{id+1},$FR.A$2:$FR.B$100,2),"")'  # fórmula coluna G
            )
            application_worksheet.write(id, 6, formula, locked_cell_format)  # Coluna G
            application_worksheet.write(id, 7, "", body_format)  # Coluna H
            formula = (
                f'=IFERROR(VLOOKUP(H{id+1},$CB.A$2:$CB.B$100,2),"")'  # fórmula coluna I
            )
            application_worksheet.write(id, 8, formula, locked_cell_format)  # Coluna I
            application_worksheet.write(id, 9, "", body_format)  # Coluna J
            formula = (
                f'=IFERROR(VLOOKUP(J{id+1},$FR.A$2:$FR.B$100,2),"")'  # fórmula coluna K
            )
            application_worksheet.write(id, 10, formula, locked_cell_format)  # Coluna K

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


if __name__ == "__main__":
    AccountabilityCSVExporter().handle()
