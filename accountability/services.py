import xlsxwriter

def export_accountability_csv():
    # 1. Pegar campos no banco
    # 2. Anaisar e transformar campos
    # 3. Gerar arquivo xlsx
    # 4. Retornar arquivo
    
    prefeitura = "Várzea Pta"
    

    # Create a workbook and add a worksheet.
    workbook = xlsxwriter.Workbook('Expenses01.xlsx')
    worksheet = workbook.add_worksheet()
    
    expenses = (
        ['Banana', 20],
        ['Mac', 22],
        ['Pera', 30],
    )
    
    row = 0
    col = 0
    
    for item, id in (expenses):
        worksheet.write(row, col, item)
        worksheet.write(row, col+1, id)
        row +=1
        
    worksheet.write(row, 0, 'Total')
    worksheet.write(row, 1, '=SUM(B1:B3)')
    
    workbook.close()
    
    return workbook

if __name__ == "__main__":
    export_accountability_csv()