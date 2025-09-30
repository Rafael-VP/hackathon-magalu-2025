# gui.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit,
    QPushButton, QCheckBox, QApplication, QTabWidget
)
from PyQt6.QtGui import QScreen

class Ui_BlockerApp(object):
    def setupUi(self, main_window):
        # --- Basic Window Setup ---
        main_window.setWindowTitle('PyQt System Blocker')
        screen = QScreen.availableGeometry(QApplication.primaryScreen())
        width = int(screen.width() * 0.4)
        height = int(screen.height() * 0.5)
        main_window.setGeometry(screen.x(), screen.y(), width, height)

        # --- Main Layout ---
        self.main_layout = QVBoxLayout(main_window)
        self.main_layout.setContentsMargins(1, 1, 1, 1)
        self.main_layout.setSpacing(0)

        # --- Custom Title Bar (Unchanged) ---
        self.title_bar = QWidget()
        self.title_bar.setObjectName("title_bar")
        self.title_bar.setFixedHeight(35)
        title_bar_layout = QHBoxLayout(self.title_bar)
        title_bar_layout.setContentsMargins(10, 0, 0, 0)
        self.title_label = QLabel('PyQt System Blocker')
        self.title_label.setObjectName("title_label")
        self.minimize_button = QPushButton("0")
        self.minimize_button.setObjectName("minimize_button")
        self.maximize_button = QPushButton("1")
        self.maximize_button.setObjectName("maximize_button")
        self.close_button = QPushButton("r")
        self.close_button.setObjectName("close_button")
        title_bar_layout.addWidget(self.title_label)
        title_bar_layout.addStretch()
        title_bar_layout.addWidget(self.minimize_button)
        title_bar_layout.addWidget(self.maximize_button)
        title_bar_layout.addWidget(self.close_button)
        self.main_layout.addWidget(self.title_bar)
        
        # --- Content Area with Padding ---
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(15, 15, 15, 15)
        self.main_layout.addWidget(content_widget)

        # --- NEW: Tab Widget for Content ---
        tabs = QTabWidget()
        
        # Tab 1: Website Blocker
        website_tab = QWidget()
        website_layout = QVBoxLayout(website_tab)
        website_layout.setContentsMargins(0, 10, 0, 0)
        self.website_list_edit = QTextEdit()
        website_layout.addWidget(QLabel('Enter websites to block (one per line):'))
        website_layout.addWidget(self.website_list_edit)
        tabs.addTab(website_tab, "Website Blocker")

        # Tab 2: Application Blocker
        app_tab = QWidget()
        app_layout = QVBoxLayout(app_tab)
        app_layout.setContentsMargins(0, 10, 0, 0)
        self.app_list_edit = QTextEdit()
        app_layout.addWidget(QLabel('Enter .exe files to block (e.g., Spotify.exe):'))
        app_layout.addWidget(self.app_list_edit)
        tabs.addTab(app_tab, "Application Blocker")
        
        content_layout.addWidget(tabs)
        
        # --- Global Controls Below Tabs ---
        self.enable_checkbox = QCheckBox('Enable All Blockers')
        self.enable_checkbox.setChecked(True)
        content_layout.addWidget(self.enable_checkbox)
        
        self.apply_button = QPushButton('Apply Changes')
        content_layout.addWidget(self.apply_button)
        
        self.status_label = QLabel('Status: Ready')
        content_layout.addWidget(self.status_label)

        # --- Attach widgets to main_window for logic access ---
        main_window.website_list_edit = self.website_list_edit
        main_window.app_list_edit = self.app_list_edit
        main_window.enable_checkbox = self.enable_checkbox
        main_window.apply_button = self.apply_button
        main_window.status_label = self.status_label