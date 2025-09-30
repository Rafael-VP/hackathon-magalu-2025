# main.py
import sys
import os
import platform
from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtCore import Qt, QPoint

# --- Conditional import for Windows Registry ---
if platform.system() == "Windows":
    import winreg

from gui import Ui_BlockerApp

# --- Constants ---
MARKER = "# MANAGED BY PYQT-BLOCKER"
REDIRECT_IP = "127.0.0.1"
DARK_THEME = """
QWidget {
    background-color: #2b2b2b; color: #f0f0f0;
    font-family: Segoe UI; font-size: 14px;
}
QWidget#title_bar { background-color: #1e1e1e; }
QLabel#title_label { font-size: 16px; font-weight: bold; padding-left: 5px; }
QPushButton {
    background-color: #555555; border: 1px solid #777777;
    padding: 8px; border-radius: 3px;
}
QPushButton:hover { background-color: #6a6a6a; }
QTextEdit {
    background-color: #3c3c3c; border: 1px solid #555555;
    border-radius: 3px; font-family: Consolas, monospaced;
}
QPushButton#minimize_button, QPushButton#maximize_button, QPushButton#close_button {
    background-color: transparent; border: none; font-family: "Webdings";
    font-size: 16px; padding: 2px;
}
QPushButton#minimize_button:hover, QPushButton#maximize_button:hover { background-color: #555555; }
QPushButton#close_button:hover { background-color: #e81123; color: white; }
QTabWidget::pane { border: 1px solid #555; }
QTabBar::tab {
    background: #2b2b2b; padding: 8px 15px;
    border: 1px solid #555; border-bottom: none;
}
QTabBar::tab:selected { background: #3c3c3c; }
"""

class BlockerApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.ui = Ui_BlockerApp()
        self.ui.setupUi(self)
        
        # --- Properties for logic ---
        self.old_pos = None
        self.hosts_path = self.get_hosts_path()
        self.helper_path = self.get_helper_path()
        self.previously_blocked_exes = set() # For tracking EXE changes
        
        self.connect_signals()
        self.load_initial_state()
        self.show()

    def connect_signals(self):
        """Connect widget signals to the master apply function."""
        self.apply_button.clicked.connect(self.apply_all_changes)
        # Window controls
        self.ui.close_button.clicked.connect(self.close)
        self.ui.minimize_button.clicked.connect(self.showMinimized)
        self.ui.maximize_button.clicked.connect(self.toggle_maximize)

    def apply_all_changes(self):
        """Master function to apply all blocking rules."""
        is_enabled = self.enable_checkbox.isChecked()
        
        # Apply website blocks
        website_blacklist = self.website_list_edit.toPlainText().split('\n')
        self.update_hosts_file(website_blacklist, is_enabled)
        
        # Apply exe blocks (only if on Windows)
        if platform.system() == "Windows":
            exe_blacklist = self.app_list_edit.toPlainText().split('\n')
            self.update_exe_blocks(exe_blacklist, is_enabled)

    def load_initial_state(self):
        """Loads all current settings from the system."""
        try:
            with open(self.hosts_path, 'r') as f:
                lines = f.readlines()
            blocked_sites, is_enabled = [], False
            for line in lines:
                if MARKER in line:
                    is_enabled = True
                    parts = line.split()
                    if len(parts) >= 2: blocked_sites.append(parts[1])
            self.website_list_edit.setText('\n'.join(blocked_sites))
            self.enable_checkbox.setChecked(is_enabled)
            self.status_label.setText("Status: Loaded hosts file.")
        except Exception as e:
            self.status_label.setText(f"Status: Error loading hosts file - {e}")

        if platform.system() == "Windows":
            self.load_exe_block_state()

    # --- Website Blocker Methods ---
    def update_hosts_file(self, blacklist, is_enabled):
        try:
            with open(self.hosts_path, 'r') as f:
                lines = [line for line in f if MARKER not in line]
            if is_enabled:
                for site in blacklist:
                    if site.strip():
                        lines.append(f"{REDIRECT_IP}\t{site.strip()}\t{MARKER}\n")
            with open(self.hosts_path, 'w') as f: f.writelines(lines)
            self.status_label.setText("Status: Hosts file updated!")
            self.status_label.setStyleSheet("color: green;")
            self.flush_dns()
        except Exception as e:
            self.status_label.setText(f"Hosts Error: {e}. Run as Admin.")
            self.status_label.setStyleSheet("color: red;")

    # --- EXE Blocker Methods (Windows Only) ---
    def load_exe_block_state(self):
        key_path = r"Software\Microsoft\Windows NT\CurrentVersion\Image File Execution Options"
        blocked_exes = set()
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path) as base_key:
                i = 0
                while True:
                    try:
                        exe_name = winreg.EnumKey(base_key, i)
                        with winreg.OpenKey(base_key, exe_name) as sub_key:
                            debugger_val, _ = winreg.QueryValueEx(sub_key, "Debugger")
                            if self.helper_path in debugger_val:
                                blocked_exes.add(exe_name)
                        i += 1
                    except OSError: break
            self.app_list_edit.setText('\n'.join(sorted(list(blocked_exes))))
            self.previously_blocked_exes = blocked_exes
        except FileNotFoundError: pass # Key doesn't exist yet
        except Exception as e: print(f"Could not load EXE state: {e}")

    def update_exe_blocks(self, blacklist, is_enabled):
        current_blacklist = {exe.strip() for exe in blacklist if exe.strip()}
        
        to_unblock = self.previously_blocked_exes - current_blacklist
        for exe in to_unblock: self.unblock_executable(exe)
        
        if is_enabled:
            to_block = current_blacklist
            for exe in to_block: self.block_executable(exe)
        else:
            to_block = set()
            for exe in self.previously_blocked_exes: self.unblock_executable(exe)
        
        self.previously_blocked_exes = to_block if is_enabled else set()
        self.status_label.setText("Status: All changes applied successfully!")
        self.status_label.setStyleSheet("color: green;")

    def block_executable(self, exe_name):
        try:
            key_path = fr"Software\Microsoft\Windows NT\CurrentVersion\Image File Execution Options\{exe_name}"
            with winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, key_path) as key:
                debugger_command = f'"{sys.executable}" "{self.helper_path}"'
                winreg.SetValueEx(key, "Debugger", 0, winreg.REG_SZ, debugger_command)
        except Exception as e: print(f"Error blocking {exe_name}: {e}")

    def unblock_executable(self, exe_name):
        try:
            key_path = fr"Software\Microsoft\Windows NT\CurrentVersion\Image File Execution Options\{exe_name}"
            winreg.DeleteKey(winreg.HKEY_LOCAL_MACHINE, key_path)
        except Exception as e: print(f"Error unblocking {exe_name}: {e}")

    # --- Helper & System Methods ---
    def get_hosts_path(self):
        return r"C:\Windows\System32\drivers\etc\hosts" if platform.system() == "Windows" else "/etc/hosts"
    def get_helper_path(self):
        return os.path.abspath(os.path.join(os.path.dirname(__file__), 'blocker_helper.pyw'))
    def flush_dns(self):
        if platform.system() == "Windows": os.system("ipconfig /flushdns")
    def toggle_maximize(self):
        if self.isMaximized(): self.showNormal()
        else: self.showMaximized()
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.ui.title_bar.underMouse(): self.old_pos = event.globalPosition().toPoint()
    def mouseMoveEvent(self, event):
        if self.old_pos:
            delta = QPoint(event.globalPosition().toPoint() - self.old_pos); self.move(self.x() + delta.x(), self.y() + delta.y()); self.old_pos = event.globalPosition().toPoint()
    def mouseReleaseEvent(self, event): self.old_pos = None

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyleSheet(DARK_THEME)
    ex = BlockerApp()
    sys.exit(app.exec())