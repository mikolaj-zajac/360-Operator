import json
import subprocess
import sys
import os
import csv
import time
from os import mkdir

from pymsgbox import alert

from hardware_handler import HardwareManager
from webp_handler import process_all
from uploader import upload_files

from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QFileDialog, QTextEdit, QVBoxLayout, QWidget, \
    QHBoxLayout, QLabel, QGridLayout, QTreeView, QMessageBox
from PyQt6.QtGui import QColor, QFileSystemModel


class FileDialogExample(QMainWindow):
    def __init__(self):
        super().__init__()
        self.selected_path = ""
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        self.target_folder = os.path.join(desktop, "Zdjecia360")
        # Create folder if it doesn't exist
        if not os.path.exists(self.target_folder):
            os.makedirs(self.target_folder)

        self.initUI()

    def initUI(self):
        self.setWindowTitle('360 Photos Explorer')
        self.setGeometry(100, 100, 800, 600)

        # Central widget and layout
        central_widget = QWidget()

        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Label showing current directory
        self.current_dir_label = QLabel(f"Current Directory: {self.target_folder}")
        layout.addWidget(self.current_dir_label)

        # Tree view for file system
        self.tree_view = QTreeView()
        self.model = QFileSystemModel()
        self.model.setRootPath(self.target_folder)
        self.tree_view.setModel(self.model)
        self.tree_view.setRootIndex(self.model.index(self.target_folder))
        self.tree_view.setSelectionMode(QTreeView.SelectionMode.SingleSelection)
        self.tree_view.selectionModel().selectionChanged.connect(self.validate_selection)
        self.tree_view.doubleClicked.connect(self.on_item_double_clicked)
        layout.addWidget(self.tree_view)

        button_layout = QGridLayout()
        #
        self.button = QPushButton("Select update file", self)
        self.button.setFixedSize(250, 50)
        self.button.clicked.connect(self.openFileDialog)
        button_layout.addWidget(self.button, 0, 1)

        self.capture_button = QPushButton("Capture Photos", self)
        self.capture_button.setFixedSize(250, 50)
        self.capture_button.clicked.connect(self.capture)
        self.capture_button.setEnabled(False)
        button_layout.addWidget(self.capture_button, 0, 0)

        self.temp = QPushButton("temp", self)
        self.temp.setFixedSize(250, 50)
        self.temp.clicked.connect(self.start_upload)
        button_layout.addWidget(self.temp, 1, 0)

        self.refresh_button = QPushButton("test", self)
        self.refresh_button.setFixedSize(250, 50)
        self.refresh_button.clicked.connect(self.test_camera)
        button_layout.addWidget(self.refresh_button, 1, 1)

        layout.addLayout(button_layout)
        #
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def capture(self):
        selected = self.tree_view.selectedIndexes()
        # print(selected)
        if not selected:
            return

        name = self.model.filePath(selected[0])
        self.selected_path = os.path.join(self.target_folder, name)
        self.capture_button.setEnabled(False)

        hw = HardwareManager(save_folder=self.selected_path)
        hw.capture_sequence(num_photos=20)
        # hw.cleanup()
        self.run_photoshop_automation()

    def test_camera(self):
        hw = HardwareManager(save_folder=self.selected_path)
        if hw.capture_dslr_photo(filename="test.jpg"):
            # messagebox.showinfo("Success", "Test photo captured successfully")
            cmd = "usbipd detach --busid=3-1;"
            subprocess.run(["powershell", "-Command", cmd])
            time.sleep(1)
            cmd = "usbipd attach --wsl --busid=3-1"
            subprocess.run(["powershell", "-Command", cmd])


    def show_alert_with_buttons(
            parent: QWidget,
            title: str,
            message: str,
            buttons=QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel,
            icon=QMessageBox.Icon.Question
    ) -> QMessageBox.StandardButton:

        msg_box = QMessageBox(parent)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setStandardButtons(buttons)
        msg_box.setIcon(icon)
        result = msg_box.exec()
        return result

    def run_photoshop_automation(self):
        win_path = os.path.abspath(self.selected_path).replace('/', '\\')

        with open("folder_path.txt", "w") as f:
            f.write(win_path)

        jsx_script = "auto_process.jsx"
        photoshop_exe = r"C:\Program Files\Adobe\Adobe Photoshop 2024\Photoshop.exe"  # Change path if needed
        print("✅ Photoshop automation started.")
        subprocess.run([
            photoshop_exe,
            jsx_script
        ], check=True)
        process_all(self.selected_path)
        self.start_upload()

    def start_upload(self):
        result = self.show_alert_with_buttons("updt", "Automatic Upload")

        if result == QMessageBox.StandardButton.Ok:
            print("Użytkownik wybrał OK")
            with open("folder_path.txt", "r") as f:
                print(f.read())

                upload_files(f.read())

        elif result == QMessageBox.StandardButton.Cancel:
            print("Użytkownik anulował")

    def validate_selection(self):
        selected = self.tree_view.selectedIndexes()
        if not selected:
            self.capture_button.setEnabled(False)
            # self.select_button.setEnabled(False)
            return
        #
        index = selected[0]
        path = self.model.filePath(index)

        is_valid = False
        if os.path.isdir(path) and not self.capture_button.isEnabled():
            has_subfolders = any(
                os.path.isdir(os.path.join(path, item))
                for item in os.listdir(path)
            )
            is_valid = not has_subfolders

        self.capture_button.setEnabled(is_valid)

    def on_item_double_clicked(self, index):
        path = self.model.filePath(index)
        if os.path.isfile(path):
            try:
                os.startfile(path)
            except:
                QMessageBox.information(self, "Info", f"Would open: {path}")

    def refresh_view(self):
        self.model.setRootPath(self.target_folder)
        self.tree_view.setRootIndex(self.model.index(self.target_folder))
        self.current_dir_label.setText(f"Current Directory: {self.target_folder}")

    def clean_name(self, name, delete):
        name_upper = name.upper()
        for item in delete:
            if item.upper() in name_upper:
                name = name.replace(item, "")
        return name.strip()

    def openFileDialog(self):
        file_dialog = QFileDialog(self)
        file_dialog.setWindowTitle("Open Files")
        file_dialog.setFileMode(QFileDialog.FileMode.ExistingFiles)
        file_dialog.setViewMode(QFileDialog.ViewMode.Detail)

        if file_dialog.exec():
            selected_files = file_dialog.selectedFiles()
            extracted_data = []
            output_text = ""

            for file_path in selected_files:
                if file_path.lower().endswith('.csv'):
                    try:
                        with open(file_path, mode='r', newline='', encoding='utf-8') as file:
                            reader = csv.DictReader(file, delimiter=',', quotechar='"')

                            for row in reader:
                                id = row.get("@id", "N/A")
                                producer = row.get('/producer@name', "N/A")
                                name = row.get('/description/name[pol]', 'N/A')
                                status = row.get('/sizes/size/stock@stock_id', 'N/A')
                                quantity = row.get('/sizes/size/stock@quantity', 'N/A')
                                param = row.get('/parameters/parameter@textid[pol]', 'N/A')
                                if "Å" in name:
                                    name = name.replace("Å", "ł")
                                if "Å¼" in name:
                                    name = name.replace("Å¼", "ż")
                                if "Ć³" in name:
                                    name = name.replace("Ć³", "ó")
                                if "Ä" in name:
                                    name = name.replace("Ä", "ą")
                                if "ozonowanie" in name.lower():
                                    continue
                                if "butów" in name.lower():
                                    continue
                                if "nakładk" in name.lower():
                                    continue
                                if "na buty" in name.lower():
                                    continue
                                if "kasków" in name.lower():
                                    continue
                                if "na kask" in name.lower():
                                    continue
                                if "ogrzewacz" in name.lower():
                                    continue
                                if "ozonowanie" in name.lower():
                                    continue
                                if "uchwyt" in name.lower():
                                    continue
                                if "but" in name.lower():
                                    type = "but"
                                if "kask" in name.lower():
                                    type = "kask"

                                if ", Wyprzedaż" in name:
                                    name = name.split(", Wyprzedaż")[0]
                                if ", Przecena" in name:
                                    name = name.split(", Przecena")[0]

                                if "ALPINESTARS" in name.upper():
                                    # jebani idioci z alpinestars
                                    delete = [" Buty motocyklowe wyścigowe",
                                              " Motocyklowe Buty wyścigowe",
                                              " Buty wyścigowe",
                                              " Motocyklowe Buty turystyczne",
                                              " Motocyklowe Buty sportowe",
                                              " Buty motocyklowe",
                                              " Buty motocyklowe",
                                              " Buty turystyczne",
                                              " Motocyklowe Buty",
                                              " Buty codzienne",
                                              " Buty sportowe",
                                              "ALPINESTARS",
                                              "Alpinestars",
                                              "wyścigowe",
                                              "sportowe",
                                              "turystyczne",
                                              "motocyklowe",
                                              "Buty ",
                                              "Buty",
                                              "Buty  "]
                                    name = self.clean_name(name, delete)
                                if producer.lower() in name.lower():
                                    name = name.lower().split(producer.lower())[1]

                                if "3" in status or "1" in status:
                                    status = status.split('\n')
                                    quantity = quantity.split('\n')

                                    for index, s in enumerate(status):
                                        if s == "3" or s == "1":
                                            if float(quantity[index]) > 0:
                                                status = True
                                                break
                                            else:
                                                status = False
                                else:
                                    status = ""
                                output_text += f"{name}\t{status}\n"
                                extracted_data.append([id, producer, name, quantity, status])

                                if r"Prezentacja 360\tak" in param:
                                    param = True
                                else:
                                    param = False

                                if not param and status:
                                    parent_directory = self.target_folder
                                    directory_name = name
                                    full_path = os.path.join(parent_directory, type, producer, directory_name)

                                    json_path = os.path.join(full_path, "data.json")

                                    data = {
                                        "id": id,
                                        "producer": producer,
                                        "done": False
                                    }

                                    try:
                                        os.makedirs(full_path, exist_ok=True)
                                        print("?")
                                        # os.mkdir(json_path)
                                        os.makedirs(os.path.dirname(json_path), exist_ok=True)
                                        with open(json_path, 'w') as f:
                                            json.dump(data, f, indent=4)
                                        print(
                                            f"Directory '{directory_name}' created successfully at '{parent_directory}'.")
                                    except FileExistsError:
                                        print(f"Directory '{directory_name}' already exists at '{parent_directory}'.")
                                    except PermissionError:
                                        print(
                                            f"Permission denied: Unable to create '{directory_name}' at '{parent_directory}'.")
                                    except Exception as e:
                                        print(f"An error occurred: {e}")



                    except Exception as e:
                        print(f"Error reading {file_path}: {e}\n")
                else:
                    print(f"{file_path} is not a CSV (.csv) file. Skipping.\n")

            if extracted_data:
                output_file = 'extracted_data.csv'
                with open(output_file, mode='w', newline='', encoding='utf-8') as output:
                    writer = csv.writer(output)
                    writer.writerow(['ID', 'Producer', 'Product Name', "Stock", 'In Stock'])
                    writer.writerows(extracted_data)

                print(f"Data has been saved to '{output_file}'.\n")

            self.text_edit.setText(output_text)

def main():

    app = QApplication(sys.argv)
    window = FileDialogExample()
    window.show()
    # keyboard.add_hotkey('f13', click_first)
    # keyboard.add_hotkey('f14', click_second)


    sys.exit(app.exec())

if __name__ == "__main__":
    main()