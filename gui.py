# gui.py

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit,
    QPushButton, QCheckBox, QApplication, QSpacerItem, QSizePolicy
)
from PyQt6.QtGui import QScreen
from PyQt6.QtCore import Qt

class Ui_BlockerApp(object):
    def setupUi(self, main_window):
        main_window.setWindowTitle('PyQt Website Blocker')
        screen = QScreen.availableGeometry(QApplication.primaryScreen())
        width = int(screen.width() * 0.4)
        height = int(screen.height() * 0.5)
        main_window.setGeometry(screen.x(), screen.y(), width, height)
        
        # The main vertical layout
        self.main_layout = QVBoxLayout(main_window)
        self.main_layout.setContentsMargins(1, 1, 1, 1) # Thin border
        self.main_layout.setSpacing(0)

        # --- START: CUSTOM TITLE BAR ---
        self.title_bar = QWidget()
        self.title_bar.setObjectName("title_bar")
        self.title_bar.setFixedHeight(35)
        title_bar_layout = QHBoxLayout(self.title_bar)
        title_bar_layout.setContentsMargins(0, 0, 0, 0)
        title_bar_layout.setSpacing(0)

        # Title Label
        self.title_label = QLabel('PyQt Website Blocker')
        self.title_label.setObjectName("title_label")

        # Window control buttons
        self.minimize_button = QPushButton("0") # Webdings font: 0=minimize
        self.minimize_button.setObjectName("minimize_button")
        self.maximize_button = QPushButton("1") # Webdings font: 1=maximize
        self.maximize_button.setObjectName("maximize_button")
        self.close_button = QPushButton("r") # Webdings font: r=close
        self.close_button.setObjectName("close_button")
        
        title_bar_layout.addWidget(self.title_label)
        title_bar_layout.addStretch() # Spacer
        title_bar_layout.addWidget(self.minimize_button)
        title_bar_layout.addWidget(self.maximize_button)
        title_bar_layout.addWidget(self.close_button)

        self.main_layout.addWidget(self.title_bar)
        # --- END: CUSTOM TITLE BAR ---

        # --- Content Area ---
        self.content_area = QWidget()
        content_layout = QVBoxLayout(self.content_area)
        content_layout.setContentsMargins(15, 15, 15, 15) # Add padding inside

        self.info_label = QLabel('Enter websites to block (one per line):')
        self.blacklist_edit = QTextEdit()
        self.enable_checkbox = QCheckBox('Enable Blocker')
        self.apply_button = QPushButton('Apply Changes')
        self.status_label = QLabel('Status: Ready')
        
        content_layout.addWidget(self.info_label)
        content_layout.addWidget(self.blacklist_edit)
        content_layout.addWidget(self.enable_checkbox)
        content_layout.addWidget(self.apply_button)
        content_layout.addWidget(self.status_label)
        
        self.main_layout.addWidget(self.content_area)
        
        # Attach widgets to main_window for logic access
        main_window.blacklist_edit = self.blacklist_edit
        main_window.enable_checkbox = self.enable_checkbox
        main_window.apply_button = self.apply_button
        main_window.status_label = self.status_label