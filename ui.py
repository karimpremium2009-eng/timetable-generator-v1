import flet as ft


class TimetableEditor(ft.Container):
    def __init__(self):
        super().__init__()
        # Mobile UI Reference Style
        self.bgcolor = "#FFFFFF"
        self.border_radius = 20
        self.padding = 15
        # FIX: Replaced ft.colors.with_opacity with Hex string "#1A000000" (10% Black)
        self.shadow = ft.BoxShadow(blur_radius=15, color="#1A000000")

        # DATA STRUCTURE: Rows=Days, Cols=Times
        self.days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        self.times = ["08:30 - 09:30", "09:30 - 10:30", "10:30 - 11:30", "11:30 - 12:30"]

        # Grid Data
        self.grid_data = [["" for _ in self.times] for _ in self.days]
        self.merges = []
        self.selected_cells = set()
        self.selection_mode = False

        # --- UI COMPONENTS ---
        self.grid_column = ft.Column(spacing=8)

        self.scrollable_grid = ft.Row(
            controls=[self.grid_column],
            scroll=ft.ScrollMode.ALWAYS,
            alignment=ft.MainAxisAlignment.START,
            vertical_alignment=ft.CrossAxisAlignment.START,
        )

        # Style Definitions
        self.btn_style = ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=12),
            padding=15,
            color="white"
        )

        # Controls
        self.btn_select = ft.IconButton("touch_app", icon_color="grey", on_click=self.toggle_mode,
                                        tooltip="Select Mode")
        self.btn_merge = ft.ElevatedButton("Merge", icon="merge_type", bgcolor="#5E35B1", color="white", disabled=True,
                                           on_click=self.apply_merge, style=self.btn_style)

        self.content = ft.Column([
            # 1. Edit Tools
            ft.Container(
                content=ft.Column([
                    # Time Management
                    ft.Row([
                        ft.Icon("access_time", size=18, color="#5E35B1"),
                        ft.Text("Time Slots (Columns)", weight="bold", color="#455A64"),
                        ft.Container(expand=True),
                        self._mini_btn("add", self.add_time, "#5E35B1"),
                        self._mini_btn("remove", self.remove_time, "#E53935"),
                    ], alignment=ft.MainAxisAlignment.CENTER),

                    ft.Divider(height=10, color="transparent"),

                    # Day Management
                    ft.Row([
                        ft.Icon("calendar_today", size=18, color="#00897B"),
                        ft.Text("School Days (Rows)", weight="bold", color="#455A64"),
                        ft.Container(expand=True),
                        self._mini_btn("add", self.add_day, "#00897B"),
                        self._mini_btn("remove", self.remove_day, "#E53935"),
                    ], alignment=ft.MainAxisAlignment.CENTER),
                ]),
                padding=15, bgcolor="#F5F7FA", border_radius=15
            ),

            ft.Divider(height=15, color="transparent"),

            # 2. Merge Tools
            ft.Container(
                content=ft.Row([
                    ft.Text("Selection:", weight="bold", color="#37474F"),
                    self.btn_select,
                    self.btn_merge,
                    ft.Container(expand=True),
                    ft.IconButton("delete_sweep", icon_color="#E53935", on_click=self.clear_merges,
                                  tooltip="Reset Merges")
                ]),
                padding=10, bgcolor="#F5F7FA", border_radius=15
            ),

            ft.Divider(height=15, color="transparent"),

            # 3. The Timetable
            ft.Text("↔️ Swipe table to see all times", size=12, italic=True, color="grey"),
            ft.Container(
                content=self.scrollable_grid,
                border_radius=10,
                padding=5,
            )
        ])

        self.render_grid(run_update=False)

    def _mini_btn(self, icon, func, color):
        return ft.Container(
            content=ft.Icon(icon, size=16, color="white"),
            bgcolor=color, width=32, height=32, border_radius=8,
            on_click=func, alignment=ft.alignment.center,
            ink=True
        )

    # --- LOGIC ---
    def is_covered(self, r, c):
        for (mr, mc, rs, cs) in self.merges:
            if mr <= r < mr + rs and mc <= c < mc + cs:
                if r == mr and c == mc: return False
                return True
        return False

    def get_span(self, r, c):
        for (mr, mc, rs, cs) in self.merges:
            if r == mr and c == mc: return rs, cs
        return 1, 1

    def render_grid(self, run_update=True):
        self.grid_column.controls.clear()

        CELL_W = 120
        CELL_H = 60
        SPACING = 8

        # --- HEADER ROW (Times) ---
        header = ft.Row(spacing=SPACING)
        header.controls.append(
            ft.Container(
                width=100, height=50, bgcolor="#ECEFF1", border_radius=10,
                content=ft.Container(content=ft.Text("DAY", size=10, weight="bold", color="#90A4AE"),
                                     alignment=ft.alignment.center)
            )
        )
        for i, t in enumerate(self.times):
            header.controls.append(
                ft.Container(
                    width=CELL_W, height=50, bgcolor="#5E35B1", border_radius=10,
                    padding=5,
                    content=ft.TextField(value=t, text_style=ft.TextStyle(size=12, color="white"),
                                         text_align=ft.TextAlign.CENTER, border=ft.InputBorder.NONE,
                                         on_change=lambda e, idx=i: self.update_time(e, idx))
                )
            )
        self.grid_column.controls.append(header)

        # --- DATA ROWS (Days) ---
        for r, day in enumerate(self.days):
            row = ft.Row(spacing=SPACING)

            row.controls.append(
                ft.Container(
                    width=100, height=CELL_H, bgcolor="#00897B", border_radius=10,
                    padding=5,
                    content=ft.TextField(value=day, text_style=ft.TextStyle(size=12, color="white", weight="bold"),
                                         text_align=ft.TextAlign.CENTER, border=ft.InputBorder.NONE,
                                         on_change=lambda e, idx=r: self.update_day(e, idx))
                )
            )

            c = 0
            while c < len(self.times):
                if self.is_covered(r, c):
                    c += 1
                    continue

                r_span, c_span = self.get_span(r, c)
                total_w = (CELL_W * c_span) + (SPACING * (c_span - 1))

                is_sel = (r, c) in self.selected_cells
                bg = "#F5F7FA" if not is_sel else "#C5E1A5"
                border = "#E0E0E0" if not is_sel else "#7CB342"

                try:
                    val = self.grid_data[r][c]
                except:
                    val = ""

                cell_ui = ft.Container(
                    width=total_w, height=CELL_H,
                    bgcolor=bg, border=ft.border.all(1, border), border_radius=10,
                    content=ft.TextField(
                        value=val, read_only=self.selection_mode,
                        text_style=ft.TextStyle(size=13), text_align=ft.TextAlign.CENTER, border=ft.InputBorder.NONE,
                        on_change=lambda e, _r=r, _c=c: self.update_cell(e, _r, _c),
                        on_focus=lambda e, _r=r, _c=c: self.cell_click(e, _r, _c)
                    ),
                    on_click=lambda e, _r=r, _c=c: self.cell_click(e, _r, _c)
                )

                row.controls.append(cell_ui)
                c += 1

            self.grid_column.controls.append(row)

        if run_update: self.update()

    # --- EVENTS ---
    def update_cell(self, e, r, c):
        if not self.selection_mode: self.grid_data[r][c] = e.control.value

    def update_day(self, e, i):
        self.days[i] = e.control.value

    def update_time(self, e, i):
        self.times[i] = e.control.value

    def add_time(self, e):
        self.times.append("00:00")
        for r in self.grid_data: r.append("")
        self.render_grid()

    def remove_time(self, e):
        if len(self.times) > 1:
            self.times.pop()
            for r in self.grid_data: r.pop()
            self.merges = []
            self.render_grid()

    def add_day(self, e):
        self.days.append("Day")
        self.grid_data.append(["" for _ in self.times])
        self.render_grid()

    def remove_day(self, e):
        if len(self.days) > 1:
            self.days.pop()
            self.grid_data.pop()
            self.merges = []
            self.render_grid()

    def toggle_mode(self, e):
        self.selection_mode = not self.selection_mode
        self.btn_select.icon_color = "green" if self.selection_mode else "grey"
        self.selected_cells.clear()
        self.btn_merge.disabled = True
        self.render_grid()

    def cell_click(self, e, r, c):
        if not self.selection_mode: return
        coord = (r, c)
        if coord in self.selected_cells:
            self.selected_cells.remove(coord)
        else:
            self.selected_cells.add(coord)
        self.btn_merge.disabled = len(self.selected_cells) < 2
        self.render_grid()

    def apply_merge(self, e):
        rows = [x[0] for x in self.selected_cells]
        cols = [x[1] for x in self.selected_cells]
        r, c = min(rows), min(cols)
        rs = max(rows) - r + 1
        cs = max(cols) - c + 1

        self.merges.append((r, c, rs, cs))
        self.toggle_mode(None)

    def clear_merges(self, e):
        self.merges = []
        self.render_grid()