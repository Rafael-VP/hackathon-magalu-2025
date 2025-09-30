# main.py
# This file contains the application's logic and connects it to the UI.

import sys
import os
import platform
from PyQt6.QtWidgets import QApplication, QWidget

# --- IMPORT THE UI FROM THE OTHER FILE ---
from gui import Ui_BlockerApp

# --- Constants ---
MARKER = "# MANAGED BY PYQT-BLOCKER"
REDIRECT_IP = "127.0.0.1"

class BlockerApp(QWidget):
    def __init__(self):
        super().__init__()
        
        # --- Create an instance of the UI and set it up ---
        self.ui = Ui_BlockerApp()
        self.ui.setupUi(self) # 'self' is the main_window QWidget

        # --- Set up the rest of the application ---
        self.hosts_path = self.get_hosts_path()
        self.connect_signals()
        self.load_initial_state()
        
        self.show()

    def connect_signals(self):
        """Connect widget signals (like button clicks) to functions."""
        self.apply_button.clicked.connect(self.apply_changes)

    def get_hosts_path(self):
        """Gets the correct hosts file path for the current OS."""
        if platform.system() == "Windows":
            return r"C:\Windows\System32\drivers\etc\hosts"
        else: # macOS or Linux
            return "/etc/hosts"

    def load_initial_state(self):
        """Loads current blocked sites from the hosts file into the GUI."""
        try:
            with open(self.hosts_path, 'r') as f:
                lines = f.readlines()
            
            blocked_sites = []
            is_enabled = False
            for line in lines:
                if MARKER in line:
                    is_enabled = True
                    parts = line.split()
                    if len(parts) >= 2:
                        blocked_sites.append(parts[1])
            
            self.blacklist_edit.setText('\n'.join(blocked_sites))
            self.enable_checkbox.setChecked(is_enabled)
            self.status_label.setText("Status: Loaded existing configuration.")
            self.status_label.setStyleSheet("color: blue;")

        except Exception as e:
            self.status_label.setText(f"Status: Error loading hosts file - {e}")
            self.status_label.setStyleSheet("color: red;")
            
    def apply_changes(self):
        """Reads the GUI state and writes it to the hosts file."""
        blacklist = self.blacklist_edit.toPlainText().split('\n')
        is_enabled = self.enable_checkbox.isChecked()
        
        try:
            with open(self.hosts_path, 'r') as f:
                lines = [line for line in f if MARKER not in line]

            if is_enabled:
                for site in blacklist:
                    if site.strip():
                        new_line = f"{REDIRECT_IP}\t{site.strip()}\t{MARKER}\n"
                        lines.append(new_line)

            with open(self.hosts_path, 'w') as f:
                f.writelines(lines)
            
            self.status_label.setText("Status: Hosts file updated successfully!")
            self.status_label.setStyleSheet("color: green;")
            self.flush_dns()

        except PermissionError:
            self.status_label.setText("Status: Permission denied. Run as Administrator.")
            self.status_label.setStyleSheet("color: red;")
        except Exception as e:
            self.status_label.setText(f"Status: An error occurred: {e}")
            self.status_label.setStyleSheet("color: red;")

    def flush_dns(self):
        """Flushes the system's DNS cache for changes to take effect."""
        os_name = platform.system()
        command = ""
        if os_name == "Windows":
            command = "ipconfig /flushdns"
        elif os_name == "Darwin": # macOS
            command = "sudo dscacheutil -flushcache; sudo killall -HUP mDNSResponder"
        elif os_name == "Linux":
            command = "sudo systemd-resolve --flush-caches"
        
        if command:
            os.system(command)
            print("DNS cache flushed.")

# This part remains the same
if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = BlockerApp()
    sys.exit(app.exec())