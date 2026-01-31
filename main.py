import flet as ft
import os
import platform
import subprocess
from ui import TimetableEditor
from pdf_generator import TimetablePDF


def main(page: ft.Page):
    # --- APP CONFIG ---
    page.title = "Timetable Pro"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0
    page.bgcolor = "#FFFFFF"

    # We manage scrolling inside the views now
    page.scroll = None

    # --- 1. ANDROID-SPECIFIC HELPERS ---
    def is_android():
        """Detect if running on Android."""
        try:
            return "ANDROID_STORAGE" in os.environ
        except:
            return False

    def get_downloads_path():
        """Returns the robust path to Downloads folder."""
        if is_android():
            # Standard Android Downloads path
            return "/storage/emulated/0/Download"
        elif platform.system() == "Windows":
            return os.path.join(os.environ["USERPROFILE"], "Downloads")
        else:
            return os.path.join(os.path.expanduser("~"), "Downloads")

    def open_file(path):
        """Opens the file intelligently based on OS."""
        try:
            if is_android():
                # On Android, we must use Flet's launch_url to trigger the intent
                page.launch_url(f"file://{path}")
            elif platform.system() == "Windows":
                os.startfile(path)
            elif platform.system() == "Darwin":  # macOS
                subprocess.call(("open", path))
            else:  # Linux
                subprocess.call(("xdg-open", path))
        except Exception as e:
            print(f"Could not open file automatically: {e}")

    # --- 2. NAVIGATION LOGIC ---

    def go_to_editor(e):
        page.clean()
        page.add(build_editor_view())
        page.update()

    def go_back_to_welcome(e):
        page.clean()
        page.add(build_welcome_view())
        page.update()

    # --- 3. VIEW BUILDERS ---

    def build_welcome_view():
        """Builds the Welcome Screen (Centered & Safe)."""
        content = ft.Container(
            expand=True,  # Forces container to fill the screen
            alignment=ft.alignment.center,  # Vertically & Horizontally Center Content
            bgcolor="white",
            content=ft.Column([
                # Icon (Using string name instead of ft.icons)
                ft.Container(
                    content=ft.Icon("school_outlined", size=80, color="#5E35B1"),
                    padding=20, border=ft.border.all(2, "#F3E5F5"), border_radius=50
                ),
                ft.Container(height=20),

                # Text
                ft.Text("School Timetable", size=28, weight="bold", color="#37474F"),
                ft.Text("Create. Merge. Export.", size=16, color="#90A4AE"),

                ft.Container(height=40),

                # Button
                ft.ElevatedButton(
                    "START CREATING",
                    on_click=go_to_editor,
                    style=ft.ButtonStyle(
                        bgcolor="#5E35B1", color="white",
                        padding={'top': 20, 'bottom': 20, 'left': 40, 'right': 40},
                        shape=ft.RoundedRectangleBorder(radius=30),
                        text_style=ft.TextStyle(size=16, weight="bold")
                    )
                ),

                ft.Container(height=60),

                # Branding
                ft.Column([
                    ft.Text("Powered by Karim Dev", size=12, weight="bold", color="#B0BEC5"),
                    ft.Text("karim.secure.dev@proton.me", size=10, color="#CFD8DC"),
                ], spacing=2, horizontal_alignment=ft.CrossAxisAlignment.CENTER)

            ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=0)
        )

        # Wrap in SafeArea to respect Android status bar
        return ft.SafeArea(content, expand=True)

    def build_editor_view():
        """Builds the Main Editor with AppBar."""

        # --- Form Components ---
        def style_input(label):
            return ft.TextField(
                label=label,
                border_radius=15,
                border_color="#E0E0E0",
                focused_border_color="#5E35B1",
                text_size=14,
                content_padding=15,
                bgcolor="#F9FAFB"
            )

        full_name = style_input("Full Name")
        class_name = style_input("Class")
        acad_year = style_input("Academic Year (e.g. 2025/2026)")
        student_no = style_input("Student Number")

        gender = ft.RadioGroup(
            content=ft.Row([
                ft.Container(content=ft.Radio(value="Male", label="Male (Navy)"), padding=10, bgcolor="#E3F2FD",
                             border_radius=10),
                ft.Container(content=ft.Radio(value="Female", label="Female (Pink)"), padding=10, bgcolor="#FCE4EC",
                             border_radius=10)
            ], alignment=ft.MainAxisAlignment.CENTER),
            value="Male"
        )

        form_card = ft.Container(
            content=ft.Column([
                ft.Text("Student Profile", size=18, weight="bold", color="#37474F"),
                ft.Divider(height=10, color="transparent"),
                full_name, class_name, acad_year, student_no,
                ft.Divider(height=10, color="transparent"),
                ft.Text("PDF Theme", size=14, color="#90A4AE"),
                gender
            ], spacing=12),
            padding=20, margin=15, bgcolor="white", border_radius=20,
            shadow=ft.BoxShadow(blur_radius=10, color="#0D000000")
        )

        editor = TimetableEditor()
        status_txt = ft.Text("", size=14, text_align="center")

        def generate(e):
            if not full_name.value:
                status_txt.value = "⚠️ Please enter your name"
                status_txt.color = "red"
                status_txt.update()
                return

            status_txt.value = "Generating..."
            status_txt.color = "blue"
            status_txt.update()

            user = {
                "name": full_name.value, "class_name": class_name.value,
                "year": acad_year.value, "serial": student_no.value,
                "gender": gender.value
            }

            # --- FILE PATH LOGIC ---
            safe_name = "".join([c if c.isalnum() else "_" for c in full_name.value])
            filename = f"Timetable_{safe_name}.pdf"

            try:
                download_dir = get_downloads_path()
                if not os.path.exists(download_dir):
                    try:
                        os.makedirs(download_dir)
                    except:
                        pass

                full_path = os.path.join(download_dir, filename)
            except:
                full_path = filename

            try:
                pdf = TimetablePDF(full_path, user, editor.days, editor.times, editor.grid_data, editor.merges)
                pdf.generate()

                status_txt.value = f"✅ Saved: {filename}"
                status_txt.color = "green"

                page.snack_bar = ft.SnackBar(ft.Text(f"Saved to Downloads: {filename}"), bgcolor="green")
                page.snack_bar.open = True

                open_file(full_path)

            except Exception as ex:
                status_txt.value = f"Error: {ex}"
                status_txt.color = "red"

            page.update()

        btn_gen = ft.Container(
            content=ft.ElevatedButton(
                "EXPORT PDF", icon="file_download",
                style=ft.ButtonStyle(
                    bgcolor="#111827", color="white", padding=20,
                    shape=ft.RoundedRectangleBorder(radius=15)
                ),
                width=300, on_click=generate
            ),
            alignment=ft.alignment.center,
            padding=ft.padding.only(bottom=50)
        )

        main_content = ft.Column(
            controls=[
                form_card,
                ft.Container(content=editor, margin=ft.margin.symmetric(horizontal=10)),
                ft.Divider(height=30, color="transparent"),
                btn_gen,
                ft.Container(content=status_txt, alignment=ft.alignment.center)
            ],
            scroll=ft.ScrollMode.AUTO,
            expand=True
        )

        # --- APP BAR & LAYOUT ---
        # FIXED: Replaced ft.icons.ARROW_BACK with "arrow_back"
        layout = ft.Column([
            ft.Container(
                bgcolor="white",
                padding=10,
                content=ft.Row([
                    ft.IconButton("arrow_back", icon_color="#37474F", on_click=go_back_to_welcome),
                    ft.Text("Edit Timetable", size=20, weight="bold", color="#37474F")
                ], alignment=ft.MainAxisAlignment.START)
            ),
            main_content
        ], expand=True, spacing=0)

        return ft.SafeArea(layout, expand=True)

    # --- START APP ---
    page.add(build_welcome_view())


if __name__ == "__main__":
    ft.app(target=main)