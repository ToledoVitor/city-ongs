import os
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from django.conf import settings
from fpdf import FPDF, XPos, YPos

from reports.exporters.base import BasePDFExporter


class BasePdf(FPDF):
    """Base PDF class with common functionality."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_auto_page_break(auto=True, margin=15)

    def footer(self):
        """Set the footer of the PDF."""
        self.set_font("FreeSans", "I", 7)
        self.set_y(-20)
        self.set_line_width(0.1)
        self.set_draw_color(0, 0, 0)

        current_datetime = datetime.now().strftime("%d/%m/%Y %H:%M")

        self.cell(w=160, h=3, text=f"Página {self.page_no()}", align="C")
        self.cell(w=30, h=3, text=(current_datetime), align="R")


# Common font paths
FONT_PATH = os.path.join(
    settings.BASE_DIR,
    "static/fonts/FreeSans.ttf",
)
FONT_BOLD_PATH = os.path.join(
    settings.BASE_DIR,
    "static/fonts/FreeSansBold.ttf",
)
FONT_ITALIC_PATH = os.path.join(
    settings.BASE_DIR,
    "static/fonts/FreeSansOblique.ttf",
)
FONT_BOLD_ITALIC_PATH = os.path.join(
    settings.BASE_DIR,
    "static/fonts/FreeSansBoldOblique.ttf",
)


@dataclass
class CommonPDFExporter(BasePDFExporter):
    """Base class for all PDF exporters with common functionality."""

    default_cell_height: int = 5
    default_font_size: int = 8
    default_fill_color: tuple = (233, 234, 236)
    default_white_color: tuple = (255, 255, 255)
    default_gray_color: tuple = (225, 225, 225)
    government_link: str = "https://doe.tce.sp.gov.br/"

    def handle(self):
        """
        Main method to generate the PDF.
        Must be implemented by subclasses.
        """
        raise NotImplementedError

    def initialize_pdf(self) -> None:
        """Initialize the PDF with common settings."""
        self.pdf = BasePdf(orientation="portrait", unit="mm", format="A4")
        self.pdf.add_page()
        self.pdf.set_margins(10, 15, 10)
        self._setup_fonts()
        self.pdf.set_font("FreeSans", size=self.default_font_size)
        self.pdf.set_fill_color(*self.default_fill_color)

    def _setup_fonts(self) -> None:
        """Setup all required fonts."""
        self.pdf.add_font("FreeSans", "", FONT_PATH, uni=True)
        self.pdf.add_font("FreeSans", "B", FONT_BOLD_PATH, uni=True)
        self.pdf.add_font("FreeSans", "I", FONT_ITALIC_PATH, uni=True)
        self.pdf.add_font("FreeSans", "BI", FONT_BOLD_ITALIC_PATH, uni=True)

    def set_font(self, font_size: int = 7, bold: bool = False) -> None:
        """Set the font style and size."""
        if bold:
            self.pdf.set_font("FreeSans", "B", font_size)
        else:
            self.pdf.set_font("FreeSans", "", font_size)

    def set_fill_color(self, gray: bool = True) -> None:
        """Set the fill color for cells."""
        if gray:
            self.pdf.set_fill_color(*self.default_fill_color)
        else:
            self.pdf.set_fill_color(*self.default_white_color)

    def draw_cell(
        self,
        text: str,
        width: int = 0,
        height: Optional[int] = None,
        align: str = "L",
        border: int = 0,
        markdown: bool = False,
        new_x: XPos = XPos.LMARGIN,
        new_y: YPos = YPos.NEXT,
    ) -> None:
        """Draw a cell with common parameters."""
        self.pdf.cell(
            w=width,
            h=height or self.default_cell_height,
            text=text,
            align=align,
            markdown=markdown,
            new_x=new_x,
            new_y=new_y,
            border=border,
        )

    def draw_multi_cell(
        self,
        text: str,
        width: int = 0,
        height: Optional[int] = None,
        align: str = "L",
        markdown: bool = False,
        new_x: XPos = XPos.LMARGIN,
        new_y: YPos = YPos.NEXT,
    ) -> None:
        """Draw a multi-cell with common parameters."""
        self.pdf.multi_cell(
            w=width,
            h=height or self.default_cell_height,
            text=text,
            align=align,
            markdown=markdown,
            new_x=new_x,
            new_y=new_y,
        )

    def draw_line(
        self,
        start_x: float,
        start_y: float,
        end_x: float,
        end_y: float,
    ) -> None:
        """Draw a line with common parameters."""
        self.pdf.line(start_x, start_y, end_x, end_y)

    def ln(self, height: Optional[int] = None) -> None:
        """Add a line break with optional height."""
        self.pdf.ln(height or self.default_cell_height)
