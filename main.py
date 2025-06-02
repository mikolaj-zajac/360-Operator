import json
import sys
import os
import csv
from os import mkdir

from key_controller import *

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

        self.select_button = QPushButton("Setup 360 Rig", self)
        # self.select_button.setEnabled(False)
        self.select_button.setFixedSize(250, 50)
        # keyboard.add_hotkey('ctrl+home', setup(selected=self.selected))
        self.select_button.clicked.connect(self.setApp)
        button_layout.addWidget(self.select_button, 0, 0)

        self.copy_button = QPushButton("Select Directory")
        self.copy_button.setEnabled(False)  # Disabled by default
        self.copy_button.setFixedSize(250, 50)
        self.copy_button.clicked.connect(self.copy_selected_name)
        button_layout.addWidget(self.copy_button, 1, 0)

        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.refresh_view)
        self.refresh_button.setFixedSize(250, 50)
        button_layout.addWidget(self.refresh_button, 1, 1)
        #
        self.create_folders_button = QPushButton("Set", self)
        self.create_folders_button.setFixedSize(250, 50)
        self.create_folders_button.clicked.connect(click_first)
        button_layout.addWidget(self.create_folders_button, 2, 0)

        self.create_folders_button = QPushButton("Start", self)
        self.create_folders_button.setFixedSize(250, 50)
        self.create_folders_button.clicked.connect(click_second)
        button_layout.addWidget(self.create_folders_button, 2, 1)
        #
        layout.addLayout(button_layout)
        #
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)
    def setApp(self):
        self.select_button.setEnabled(False)
        setup()
    def validate_selection(self):
        selected = self.tree_view.selectedIndexes()
        if not selected:
            self.copy_button.setEnabled(False)
            # self.select_button.setEnabled(False)
            return

        index = selected[0]
        path = self.model.filePath(index)

        is_valid = False
        if os.path.isfile(path):
            is_valid = True
        elif os.path.isdir(path):
            has_subfolders = any(
                os.path.isdir(os.path.join(path, item))
                for item in os.listdir(path)
            )
            is_valid = not has_subfolders

        self.copy_button.setEnabled(is_valid)

    def on_item_double_clicked(self, index):
        path = self.model.filePath(index)
        if os.path.isfile(path):
            try:
                os.startfile(path)
            except:
                QMessageBox.information(self, "Info", f"Would open: {path}")

    def copy_selected_name(self):
        selected = self.tree_view.selectedIndexes()
        # print(selected)
        if not selected:
            return

        name = self.model.filePath(selected[0])
        self.selected_path = os.path.join(self.target_folder, name)
        print(self.selected_path)
        self.selected_path = self.selected_path.replace("C:/Users/Cinek/Desktop/Zdjecia360/", "")
        open_file(self.selected_path)
        # QApplication.clipboard().setText(name)
        # QMessageBox.information(self, "Copied", f"Copied: {name}")

    def refresh_view(self):
        self.model.setRootPath(self.target_folder)
        self.tree_view.setRootIndex(self.model.index(self.target_folder))
        self.current_dir_label.setText(f"Current Directory: {self.target_folder}")

    def copy_to_clipboard(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.text_edit.toPlainText())

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
    keyboard.add_hotkey('f13', click_first)
    keyboard.add_hotkey('f14', click_second)


    sys.exit(app.exec())


if __name__ == "__main__":
    main()