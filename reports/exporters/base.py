import logging
import weakref
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class BasePDFExporter:
    """
    Classe base para todos os exportadores PDF com gerenciamento adequado de recursos.
    """

    _pdf_instances = (
        weakref.WeakSet()
    )  # Rastreia todas as instâncias PDF ativas

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
        Limpa recursos do PDF de forma segura.
        """
        try:
            if self.pdf:
                self.pdf.close()
                self.pdf = None
        except Exception as e:
            logger.error(f"Erro ao limpar recursos do PDF: {e}")

    @classmethod
    def cleanup_all(cls):
        """
        Limpa recursos de todas as instâncias PDF ativas.
        """
        for instance in list(cls._pdf_instances):
            instance.cleanup()

    def initialize_pdf(self):
        """
        Inicializa o PDF com configurações básicas.
        Deve ser implementado pelas classes filhas.
        """
        raise NotImplementedError

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
