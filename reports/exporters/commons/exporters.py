from datetime import datetime

from fpdf import FPDF


class BasePdf(FPDF):
    def footer(self, *args, **kwargs):
        self.set_font("Helvetica", "I", 7)
        self.set_y(-23)
        self.set_line_width(0.1)
        self.set_draw_color(0, 0, 0)
        current_datetime = datetime.now().strftime("%d/%m/%Y %H:%M")
        self.cell(w=160, h=3, text=f"Página {self.page_no()}", align="C")
        self.cell(w=30, h=3, text=(current_datetime), align="R")