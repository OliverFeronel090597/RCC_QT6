import os
import sys
import shutil
import subprocess
from PIL import Image
from PyQt6.QtWidgets import (
    QApplication, QWidget, QPushButton, QFileDialog,
    QVBoxLayout, QHBoxLayout, QLabel, QPlainTextEdit, QStyle
)
from PyQt6.QtCore import Qt, QDateTime
from PyQt6.QtGui import QTextCharFormat, QTextCursor, QColor, QIcon
from libs.StyleUtils import apply_stylesheet
from libs.resources import *


class RccAuto(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("RCC Resource Creator")
        self.setMinimumSize(800, 500)

        self.setWindowIcon(QIcon(self.get_qt_icon("SP_TitleBarMenuButton")))

        apply_stylesheet(self, ":/resources/light.qss")

        self.label = QLabel(f"Path: {os.getcwd()}")
        self.output_text = QPlainTextEdit(readOnly=True)

        self.btn_choose_folder = QPushButton("Choose Folder")
        self.btn_choose_folder.clicked.connect(self.select_folder)

        self.btn_convert_images = QPushButton("Convert to .png")
        self.btn_convert_images.clicked.connect(self.convert_images)

        self.btn_generate_qrc = QPushButton("Generate .qrc")
        self.btn_generate_qrc.clicked.connect(self.generate_qrc_file)

        self.btn_compile_resource = QPushButton("Compile resource")
        self.btn_compile_resource.clicked.connect(self.compile_qrc_to_py)

        self.btn_fix_pyqt = QPushButton("Convert to PyQt6")
        self.btn_fix_pyqt.clicked.connect(self.convert_imports_to_pyqt6)

        # Layouts
        text_layout = QVBoxLayout()
        text_layout.addWidget(self.label)
        text_layout.addWidget(self.output_text)

        button_layout = QVBoxLayout()
        button_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        for btn in [self.btn_choose_folder, self.btn_convert_images, self.btn_generate_qrc, self.btn_compile_resource, self.btn_fix_pyqt]:
            button_layout.addWidget(btn)

        main_layout = QHBoxLayout()
        main_layout.addLayout(text_layout)
        main_layout.addLayout(button_layout)
        self.setLayout(main_layout)

        self.append_text("Application started.", "red")

    def get_qt_icon(self, icon_name):
        icon_enum = getattr(QStyle.StandardPixmap, icon_name)
        return QApplication.style().standardIcon(icon_enum).pixmap(32, 32)

    def get_selected_path(self):
        path = self.label.text().replace("Path:", "").strip()
        return path if os.path.isdir(path) else None

    def append_text(self, message, color="blue"):
        timestamp = QDateTime.currentDateTime().toString("HH:mm:ss") #toString("yyyy-MM-dd HH:mm:ss")
        cursor = self.output_text.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)

        fmt_time = QTextCharFormat()
        fmt_time.setForeground(QColor("black"))
        cursor.insertText(f"[{timestamp}] : ", fmt_time)

        fmt_msg = QTextCharFormat()
        fmt_msg.setForeground(QColor(color))
        cursor.insertText(message + "\n", fmt_msg)
        self.output_text.setTextCursor(cursor)


    def select_folder(self):
        self.append_text(">> Clicked: Choose Folder", "gray")
        path = QFileDialog.getExistingDirectory(self, "Select Folder")
        if path:
            self.label.setText(f"Path: {path}")
            self.append_text(f"Selected folder: {path}", "orange")
        else:
            self.append_text("No folder selected.", "red")


    def convert_images(self):
        self.append_text("--- Starting Image Conversion ---", "gray")
        folder = self.get_selected_path()
        if not folder:
            self.append_text("No valid folder path found. Conversion aborted.", "red")
            return

        supported_extensions = (".jpg", ".jpeg", ".bmp", ".gif", ".tiff", ".webp")
        original_dir = os.path.join(folder, "original")
        os.makedirs(original_dir, exist_ok=True)

        image_count = 0
        skipped = 0

        for filename in os.listdir(folder):
            if filename.lower().endswith(supported_extensions):
                image_count += 1
                input_path = os.path.join(folder, filename)
                output_file = os.path.splitext(filename)[0] + ".png"
                output_path = os.path.join(folder, output_file)

                self.append_text(f"Processing: {filename}", "orange")

                try:
                    with Image.open(input_path) as img:
                        img.convert("RGBA").save(output_path, "PNG")
                    if os.path.exists(os.path.join(original_dir, filename)):
                        os.remove(os.path.join(original_dir, filename))
                        self.append_text(f"Removed duplicate in 'original': {filename}", "gray")
                    shutil.move(input_path, os.path.join(original_dir, filename))
                    self.append_text(f"Converted and moved: {filename}", "green")
                except Exception as e:
                    self.append_text(f"Error converting {filename}: {e}", "red")
            else:
                skipped += 1

        self.append_text(f"--- Conversion Complete: {image_count} image(s) converted, {skipped} skipped ---", "blue")


    def generate_qrc_file(self):
        self.append_text("--- Generating .qrc File ---", "gray")
        folder = self.get_selected_path()
        if not folder:
            self.append_text("No valid folder path found. .qrc generation aborted.", "red")
            return
        try:
            # Add more valid Qt resource extensions here
            valid_extensions = (".png", ".jpg", ".jpeg", ".svg", ".ico", ".qss", ".ttf", ".otf", ".wav", ".mp3")
            
            resource_files = [
                f for f in os.listdir(folder)
                if os.path.isfile(os.path.join(folder, f)) and f.lower().endswith(valid_extensions)
            ]

            if not resource_files:
                self.append_text("No valid resource files found (.png, .qss, etc.).", "red")
                return

            output_qrc = os.path.join(folder, "resources.qrc")
            with open(output_qrc, "w", encoding="utf-8") as f:
                f.write("<RCC>\n  <qresource prefix=\"/resources\">\n")
                for file in resource_files:
                    f.write(f"    <file>{file}</file>\n")
                f.write("  </qresource>\n</RCC>\n")

            self.append_text(f".qrc generated: {output_qrc}", "green")
            self.append_text(f"Included {len(resource_files)} file(s): {', '.join(sorted(valid_extensions))}", "blue")
        except Exception as e:
            self.append_text(f"Failed to generate .qrc: {e}", "red")

    def resource_path(self, relative_path):
        try:
            # When running as a PyInstaller bundle
            base_path = sys._MEIPASS
        except AttributeError:
            # When running as a normal Python script
            base_path = os.path.abspath(".")
        return os.path.join(base_path, relative_path)

    def compile_qrc_to_py(self):
        self.append_text("--- Compiling .qrc to .py ---", "gray")
        folder = self.get_selected_path()
        if not folder:
            self.append_text("No valid folder path found. Compilation aborted.", "red")
            return

        qrc_file = os.path.join(folder, "resources.qrc")
        py_file = os.path.join(folder, "resources.py")

        if not os.path.exists(qrc_file):
            self.append_text(f".qrc file not found: {qrc_file}", "red")
            return

        # Use resolved path to rcc.exe from bin folder
        rcc_path = self.resource_path("bin/rcc.exe")

        # Wrap path in quotes for Windows if needed
        cmd = f'"{rcc_path}" -g python "{qrc_file}" -o "{py_file}"'

        self.append_text(f"Running command: {cmd}", "gray")
        self.run_shell_command(cmd)

    def run_shell_command(self, command):
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                self.append_text("Command executed successfully.", "green")
                self.append_text(result.stdout.strip(), "blue")
            else:
                self.append_text("Command failed:", "red")
                self.append_text(result.stderr.strip(), "red")
        except Exception as e:
            self.append_text(f"Subprocess error: {e}", "red")

    def convert_imports_to_pyqt6(self):
        self.append_text("--- Converting imports to PyQt6 ---", "gray")
        path = os.path.join(self.get_selected_path(), "resources.py")
        if not os.path.exists(path):
            self.append_text("resources.py not found in selected folder.", "red")
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            updated_lines = []
            modified = False

            for line in lines:
                if "PySide6" in line or "PyQt5" in line:
                    if not line.strip().startswith("#"):
                        line = line.replace("PySide6", "PyQt6").replace("PyQt5", "PyQt6")
                        modified = True
                updated_lines.append(line)

            with open(path, "w", encoding="utf-8") as f:
                f.writelines(updated_lines)

            if modified:
                self.append_text("Successfully updated imports to PyQt6.", "green")
            else:
                self.append_text("No changes made. Already using PyQt6.", "blue")
        except Exception as e:
            self.append_text(f"Failed to update imports: {e}", "red")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = RccAuto()
    window.show()
    sys.exit(app.exec())
