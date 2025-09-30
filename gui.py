# gui.py
# This file defines the visual layout of the application.

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTextEdit,
    QPushButton, QCheckBox, QStyleFactory, QApplication
)

class Ui_BlockerApp(object):
    def setupUi(self, main_window):
        """Sets up the UI widgets and layout on the main_window."""
        main_window.setWindowTitle('PyQt Website Blocker')
        main_window.setGeometry(300, 300, 400, 300)
        
        # Use a consistent style
        QApplication.setStyle(QStyleFactory.create('Fusion'))

        # Layout
        layout = QVBoxLayout()

        # --- Create Widgets ---
        self.title_label = QLabel('Website Blocker')
        self.title_label.setStyleSheet("font-size: 16px; font-weight: bold;")

        self.info_label = QLabel('Enter websites to block (one per line):')

        self.blacklist_edit = QTextEdit()

        self.enable_checkbox = QCheckBox('Enable Blocker')
        self.enable_checkbox.setChecked(True)

        self.apply_button = QPushButton('Apply Changes')

        self.status_label = QLabel('Status: Ready')
        self.status_label.setStyleSheet("color: grey;")

        # --- Add widgets to layout ---
        layout.addWidget(self.title_label)
        layout.addWidget(self.info_label)
        layout.addWidget(self.blacklist_edit)
        layout.addWidget(self.enable_checkbox)
        layout.addWidget(self.apply_button)
        layout.addWidget(self.status_label)
        
        main_window.setLayout(layout)

        # We attach the widgets to the main_window object so main.py can access them
        main_window.blacklist_edit = self.blacklist_edit
        main_window.enable_checkbox = self.enable_checkbox
        main_window.apply_button = self.apply_button
        main_window.status_label = self.status_label