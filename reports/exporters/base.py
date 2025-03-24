import logging
import weakref
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class BasePDFExporter:
    """
    Base class for all PDF exporters with proper resource management.
    """

    _pdf_instances = weakref.WeakSet()  # Tracks all active PDF instances

    def __init__(self):
        self.pdf = None
        self._pdf_instances.add(self)

    def __del__(self):
        """
        Ensure that the PDF resources are released when the object
        is destroyed.
        """
        self.cleanup()

    def cleanup(self):
        """
        Clean up PDF resources safely.
        """
        try:
            if self.pdf:
                self.pdf.close()
                self.pdf = None
        except Exception as exception:
            logger.error(
                "Error cleaning up PDF resources: %s", exception
            )

    @classmethod
    def cleanup_all(cls):
        """
        Clean up resources from all active PDF instances.
        """
        for instance in list(cls._pdf_instances):
            instance.cleanup()

    def initialize_pdf(self):
        """
        Initialize the PDF with basic configurations.
        Must be implemented by subclasses.
        """
        raise NotImplementedError

    def handle(self):
        """
        Main method to generate the PDF.
        Must be implemented by subclasses.
        """
        raise NotImplementedError

    def __enter__(self):
        """
        Support for use with context manager.
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Ensure cleanup of resources when exiting the context manager.
        """
        self.cleanup()
