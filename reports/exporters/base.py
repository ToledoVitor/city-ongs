import weakref

from reports.exporters.commons.exporters import BasePdf


class BasePDFExporter:
    """
    Classe base para todos os exportadores PDF com gerenciamento adequado de recursos.
    """

    default_cell_height = 5
    _pdf_instances = weakref.WeakSet()  # Rastreia todas as instâncias PDF ativas

    def __init__(self):
        self.pdf = None
        self._pdf_instances.add(self)

    def __del__(self):
        """
        Garante que os recursos do PDF sejam liberados quando o objeto for destruído.
        """
        self.cleanup()

    def cleanup(self):
        """
        Libera a referência ao PDF em memória.
        """
        # fpdf2 não expõe um método close() — o documento vive só em memória
        # (fica pronto pra descarte assim que `.output()` é chamado), então
        # não há recurso de SO pra fechar aqui.
        self.pdf = None

    @classmethod
    def cleanup_all(cls):
        """
        Limpa recursos de todas as instâncias PDF ativas.
        """
        for instance in list(cls._pdf_instances):
            instance.cleanup()

    def initialize_pdf(self, font_specs, base_font_size=None, fill_color=None):
        """
        Monta o PDF base (A4, retrato, margens padrão) e registra as fontes.

        font_specs: iterável de tuplas (style, path) para `fpdf2.add_font`,
            ex. [("", font_path), ("B", font_bold_path)].
        base_font_size: se informado, chama set_font("FreeSans", "", base_font_size)
            logo após registrar as fontes — alguns exportadores não definem uma
            fonte inicial (o primeiro `_draw_*` já define antes de escrever).
        fill_color: se informado, tupla RGB para o `set_fill_color` inicial.
        """
        pdf = BasePdf(orientation="portrait", unit="mm", format="A4")
        pdf.add_page()
        pdf.set_margins(10, 15, 10)
        for style, path in font_specs:
            pdf.add_font("FreeSans", style, path, uni=True)
        if base_font_size is not None:
            pdf.set_font("FreeSans", "", base_font_size)
        if fill_color is not None:
            pdf.set_fill_color(*fill_color)
        self.pdf = pdf
        return pdf

    def _set_font(self, font_size=7, bold=False):
        if bold:
            self.pdf.set_font("FreeSans", "B", font_size)
        else:
            self.pdf.set_font("FreeSans", "", font_size)

    def handle(self):
        """
        Método principal para gerar o PDF.
        Deve ser implementado pelas classes filhas.
        """
        raise NotImplementedError

    def __enter__(self):
        """
        Suporte para uso com context manager.
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Garante limpeza de recursos ao sair do context manager.
        """
        self.cleanup()
