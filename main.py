# main.py

import sys
import os
import platform
from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtCore import Qt, QPoint

# --- IMPORT THE UI FROM THE OTHER FILE ---
from gui import Ui_BlockerApp

# --- CONSTANTS & STYLESHEET (keep these the same) ---
MARKER = "# MANAGED BY PYQT-BLOCKER"
REDIRECT_IP = "127.0.0.1"
DARK_THEME = """
QWidget {
    background-color: #2b2b2b;
    color: #f0f0f0;
    font-family: Segoe UI;
    font-size: 14px;
}
/* Style for the custom title bar */
QWidget#title_bar {
    background-color: #1e1e1e;
}
QLabel#title_label {
    font-size: 16px;
    font-weight: bold;
    padding-left: 5px;
}
QPushButton {
    background-color: #555555;
    border: 1px solid #777777;
    padding: 5px;
    border-radius: 3px;
}
QPushButton:hover { background-color: #6a6a6a; }
QPushButton:pressed { background-color: #4f4f4f; }
QTextEdit {
    background-color: #3c3c3c;
    border: 1px solid #555555;
    border-radius: 3px;
}
/* Style for the custom window control buttons */
QPushButton#minimize_button, QPushButton#maximize_button, QPushButton#close_button {
    background-color: transparent;
    border: none;
    font-family: "Webdings"; /* Using a font with symbols */
    font-size: 16px;
    padding: 2px;
}
QPushButton#minimize_button:hover { background-color: #555555; }
QPushButton#maximize_button:hover { background-color: #555555; }
QPushButton#close_button { color: #f0f0f0; }
QPushButton#close_button:hover { background-color: #e81123; color: white; }
"""

class BlockerApp(QWidget):
    def __init__(self):
        super().__init__()
        
        # --- MAKE THE WINDOW FRAMELESS ---
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        
        self.ui = Ui_BlockerApp()
        self.ui.setupUi(self)
        
        # --- LOGIC FOR DRAGGING THE FRAMELESS WINDOW ---
        self.old_pos = None

        self.hosts_path = self.get_hosts_path()
        self.connect_signals()
        self.load_initial_state()
        
        self.show()

    # --- Re-implement mouse events to allow dragging ---
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            # Check if the click is within the title bar area
            if self.ui.title_bar.underMouse():
                self.old_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if self.old_pos:
            delta = QPoint(event.globalPosition().toPoint() - self.old_pos)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = event.globalPosition().toPoint()
            
    def mouseReleaseEvent(self, event):
        self.old_pos = None
    # --- End of dragging logic ---

    def connect_signals(self):
        """Connect widget signals to functions."""
        self.apply_button.clicked.connect(self.apply_changes)
        
        # --- Connect the new custom window buttons ---
        self.ui.close_button.clicked.connect(self.close)
        self.ui.minimize_button.clicked.connect(self.showMinimized)
        # Note: A proper maximize would require more logic to handle state changes.
        # This button is for demonstration.
        self.ui.maximize_button.clicked.connect(self.toggle_maximize)

    def toggle_maximize(self):
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    # The rest of your logic methods (get_hosts_path, apply_changes, etc.)
    # remain exactly the same. They are omitted here for brevity.
    def get_hosts_path(self):
        if platform.system() == "Windows": return r"C:\Windows\System32\drivers\etc\hosts"
        else: return "/etc/hosts"
    def load_initial_state(self):
        try:
            with open(self.hosts_path, 'r') as f: lines = f.readlines()
            blocked_sites, is_enabled = [], False
            for line in lines:
                if MARKER in line:
                    is_enabled = True
                    parts = line.split()
                    if len(parts) >= 2: blocked_sites.append(parts[1])
            self.blacklist_edit.setText('\n'.join(blocked_sites))
            self.enable_checkbox.setChecked(is_enabled)
            self.status_label.setText("Status: Loaded existing configuration.")
            self.status_label.setStyleSheet("color: #55aaff;")
        except Exception as e:
            self.status_label.setText(f"Status: Error loading hosts file - {e}")
            self.status_label.setStyleSheet("color: #ff5555;")
    def apply_changes(self):
        blacklist = self.blacklist_edit.toPlainText().split('\n')
        is_enabled = self.enable_checkbox.isChecked()
        try:
            with open(self.hosts_path, 'r') as f: lines = [line for line in f if MARKER not in line]
            if is_enabled:
                for site in blacklist:
                    if site.strip(): lines.append(f"{REDIRECT_IP}\t{site.strip()}\t{MARKER}\n")
            with open(self.hosts_path, 'w') as f: f.writelines(lines)
            self.status_label.setText("Status: Hosts file updated successfully!")
            self.status_label.setStyleSheet("color: #55ff7f;")
            self.flush_dns()
        except PermissionError:
            self.status_label.setText("Status: Permission denied. Run as Administrator.")
            self.status_label.setStyleSheet("color: #ff5555;")
        except Exception as e:
            self.status_label.setText(f"Status: An error occurred: {e}")
            self.status_label.setStyleSheet("color: #ff5555;")
    def flush_dns(self):
        os_name = platform.system()
        command = ""
        if os_name == "Windows": command = "ipconfig /flushdns"
        elif os_name == "Darwin": command = "sudo dscacheutil -flushcache; sudo killall -HUP mDNSResponder"
        elif os_name == "Linux": command = "sudo systemd-resolve --flush-caches"
        if command: os.system(command)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyleSheet(DARK_THEME)
    ex = BlockerApp()
    sys.exit(app.exec())