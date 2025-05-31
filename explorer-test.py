import os
import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QTreeView,
                             QVBoxLayout, QWidget, QPushButton, QLabel, QMessageBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFileSystemModel


class FileExplorer(QMainWindow):
    def __init__(self):
        super().__init__()
        # Get desktop path and target folder
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

        # Buttons
        self.copy_button = QPushButton("Copy Selected Name")
        self.copy_button.setEnabled(False)  # Disabled by default
        self.copy_button.clicked.connect(self.copy_selected_name)
        layout.addWidget(self.copy_button)

        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.refresh_view)
        layout.addWidget(self.refresh_button)

    def validate_selection(self):
        """Check if selected item is a valid leaf folder or file"""
        selected = self.tree_view.selectedIndexes()
        if not selected:
            self.copy_button.setEnabled(False)
            return

        index = selected[0]
        path = self.model.filePath(index)

        # Enable copy button only for:
        # 1. Files, or
        # 2. Folders that don't contain other folders (leaf folders)
        is_valid = False
        if os.path.isfile(path):
            is_valid = True
        elif os.path.isdir(path):
            # Check if folder contains any subfolders
            has_subfolders = any(
                os.path.isdir(os.path.join(path, item))
                for item in os.listdir(path)
            )
            is_valid = not has_subfolders

        self.copy_button.setEnabled(is_valid)

    def on_item_double_clicked(self, index):
        """Handle double-click on items"""
        path = self.model.filePath(index)
        if os.path.isfile(path):
            try:
                os.startfile(path)
            except:
                QMessageBox.information(self, "Info", f"Would open: {path}")

    def copy_selected_name(self):
        """Copy single selected name to clipboard"""
        selected = self.tree_view.selectedIndexes()
        if not selected:
            return

        name = os.path.basename(self.model.filePath(selected[0]))
        QApplication.clipboard().setText(name)
        QMessageBox.information(self, "Copied", f"Copied: {name}")

    def refresh_view(self):
        """Refresh the file view"""
        self.model.setRootPath(self.target_folder)
        self.tree_view.setRootIndex(self.model.index(self.target_folder))
        self.current_dir_label.setText(f"Current Directory: {self.target_folder}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FileExplorer()
    window.show()
    sys.exit(app.exec())