from datetime import datetime

from fpdf import FPDF


class ContractProgressPDFExporter:
    """
    Returns a PDF file with the contract progress report
    DOC: https://py-pdf.github.io/fpdf2/index.html
    """

    # Cores aqui
    black = (0, 0, 0)
    white = (255, 255, 255)
    blue = (0, 0, 255)

    pdf = None

    def handle(self, contract_id):
        self._set_pdf_base()
        self._build_header()
        self._build_content()
        self._build_footer()

        self.pdf.output(f"progress-report-{str(datetime.now().time())[0:8]}.pdf")
        return self.pdf

    def _set_pdf_base(self):
        self.pdf = FPDF(orientation="P", unit="mm", format="A4")
        self.pdf.set_margins(left=25, top=20, right=25)
        self.pdf.set_auto_page_break(True, margin=10)
        self.pdf.add_page()

    def _build_header(self):
        # Formatação cabecalho
        # Tem imagem? Só texto
        ...

    def _build_content(self):
        # Formatação conteudo
        self.pdf.set_font("helvetica", size=12)
        self.pdf.cell(text="hello world")

    def _build_footer(self):
        # Formatação rodapé
        ...


if __name__ == "__main__":
    ContractProgressPDFExporter().handle(contract_id=None)
