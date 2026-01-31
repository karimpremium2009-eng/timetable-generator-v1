from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.lib.units import mm


class PDFTheme:
    def __init__(self, gender):
        if gender == "Female":
            # FIXED: Elegant, High-Contrast Female Theme
            self.header_bg = HexColor("#F8BBD0")  # Soft Rose (Darker for header)
            self.label_bg = HexColor("#FCE4EC")  # Very Light Pink (Row Labels)
            self.cell_bg = HexColor("#FFF9FB")  # Near White Pink (Grid)
            self.cell_bg_alt = HexColor("#FFFFFF")  # White
            self.text_main = HexColor("#4A2C2A")  # Dark Warm Brown (High Contrast)
            self.text_header = HexColor("#4A2C2A")  # Dark Text on Pink Header
            self.border = HexColor("#F48FB1")  # Soft Pink Border
        else:
            # Male: Modern Navy & Blue
            self.header_bg = HexColor("#1A2B4C")  # Navy
            self.label_bg = HexColor("#E3F2FD")  # Light Blue
            self.cell_bg = HexColor("#F5F9FF")  # Ice Blue
            self.cell_bg_alt = HexColor("#FFFFFF")
            self.text_main = HexColor("#1A2B4C")  # Navy Text
            self.text_header = HexColor("#FFFFFF")  # White Text on Navy
            self.border = HexColor("#90CAF9")


class TimetablePDF:
    def __init__(self, filename, user_data, days, times, grid_data, merges):
        self.filename = filename
        self.user_data = user_data
        self.days = days  # Rows
        self.times = times  # Columns
        self.grid_data = grid_data
        self.merges = merges
        self.theme = PDFTheme(user_data['gender'])

        self.width, self.height = landscape(A4)
        self.margin = 15 * mm
        self.c = canvas.Canvas(filename, pagesize=landscape(A4))

    def draw_rounded_rect(self, x, y, w, h, color, radius=4):
        self.c.setFillColor(color)
        self.c.setStrokeColor(color)
        self.c.roundRect(x, y, w, h, radius, fill=1, stroke=0)

    def draw_text(self, text, x, y, w, h, color, font="Helvetica", size=10, align="center"):
        self.c.setFillColor(color)
        self.c.setFont(font, size)
        text_w = self.c.stringWidth(text, font, size)

        if align == "center":
            tx = x + (w - text_w) / 2
        elif align == "left":
            tx = x + 2 * mm

        # Vertical center approx
        ty = y + (h / 2) - (size / 3)
        self.c.drawString(tx, ty, text)

    def get_merge_span(self, r, c):
        for (mr, mc, rs, cs) in self.merges:
            if r == mr and c == mc: return rs, cs
        return 1, 1

    def is_covered(self, r, c):
        for (mr, mc, rs, cs) in self.merges:
            if mr <= r < mr + rs and mc <= c < mc + cs:
                if r == mr and c == mc: return False
                return True
        return False

    def generate(self):
        c = self.c

        # --- 1. HEADER SECTION ---
        # Left: Title
        c.setFont("Helvetica-Bold", 26)
        c.setFillColor(self.theme.text_main)
        c.drawString(self.margin, self.height - 25 * mm, "School Timetable")

        # Right: Academic Year
        c.setFont("Helvetica", 14)
        c.setFillColor(self.theme.text_main)
        year_txt = f"Academic Year: {self.user_data['year']}"
        c.drawRightString(self.width - self.margin, self.height - 25 * mm, year_txt)

        # --- 2. STUDENT INFO CARD ---
        card_y = self.height - 50 * mm
        card_h = 18 * mm
        card_w = self.width - (2 * self.margin)

        self.draw_rounded_rect(self.margin, card_y, card_w, card_h, self.theme.label_bg, radius=6)

        # Text Info
        info_text = f"NAME: {self.user_data['name'].upper()}      CLASS: {self.user_data['class_name']}      STUDENT ID: {self.user_data['serial']}"
        self.draw_text(info_text, self.margin, card_y, card_w, card_h, self.theme.text_main, font="Helvetica-Bold",
                       size=11)

        # --- 3. GRID LAYOUT ---
        start_y = card_y - 8 * mm
        grid_w = self.width - (2 * self.margin)
        grid_h = start_y - self.margin

        # Dimensions
        n_cols = len(self.times) + 1  # +1 for Day Label
        n_rows = len(self.days) + 1  # +1 for Time Header

        col_w = grid_w / n_cols
        row_h = min(grid_h / n_rows, 22 * mm)  # Cap height for elegance

        # Base Y for the grid (Top of the grid)
        current_y = start_y - row_h

        # --- A. TIME HEADERS (Top Row) ---
        # Corner Cell
        self.draw_rounded_rect(self.margin, current_y, col_w - 1 * mm, row_h - 1 * mm, self.theme.header_bg)
        self.draw_text("DAY / TIME", self.margin, current_y, col_w, row_h, self.theme.text_header,
                       font="Helvetica-Bold", size=9)

        # Time Columns
        for i, time_lbl in enumerate(self.times):
            x = self.margin + ((i + 1) * col_w)
            self.draw_rounded_rect(x, current_y, col_w - 1 * mm, row_h - 1 * mm, self.theme.header_bg)
            self.draw_text(time_lbl, x, current_y, col_w, row_h, self.theme.text_header, font="Helvetica-Bold", size=9)

        # --- B. DAY ROWS ---
        for r_idx, day_lbl in enumerate(self.days):
            current_y -= row_h

            # Day Label (Left Column)
            self.draw_rounded_rect(self.margin, current_y, col_w - 1 * mm, row_h - 1 * mm, self.theme.header_bg)
            self.draw_text(day_lbl, self.margin, current_y, col_w, row_h, self.theme.text_header, font="Helvetica-Bold",
                           size=10)

            # Cells
            for c_idx in range(len(self.times)):
                if self.is_covered(r_idx, c_idx): continue

                r_span, c_span = self.get_merge_span(r_idx, c_idx)

                # Coords
                x = self.margin + ((c_idx + 1) * col_w)

                # Calculate Merged Size
                # Width = (cols * w) - gap
                cell_w_total = (col_w * c_span) - 1 * mm
                # Height = (rows * h) - gap
                # Note: Y goes UP. If we span 2 rows down, Y needs to drop.
                # Standard Y is current_y.
                # If spanning 2 rows, height increases downwards.
                # But current_y is the BOTTOM of the row? No, in ReportLab rect is (x,y,w,h).
                # My logic: current_y is the bottom of the current row.
                # So if span > 1, we need to lower y by (r_span-1)*row_h

                cell_h_total = (row_h * r_span) - 1 * mm
                cell_y_adjusted = current_y - ((r_span - 1) * row_h)

                # Content
                try:
                    val = self.grid_data[r_idx][c_idx]
                except:
                    val = ""

                bg = self.theme.cell_bg if val.strip() else HexColor("#FDFDFD")
                if (r_idx + c_idx) % 2 == 1 and not val.strip(): bg = HexColor("#F9F9F9")  # Subtle checker

                self.draw_rounded_rect(x, cell_y_adjusted, cell_w_total, cell_h_total, bg)
                self.draw_text(val, x, cell_y_adjusted, cell_w_total, cell_h_total, self.theme.text_main, size=10)

        c.save()