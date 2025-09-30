import sys
import os
import platform
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QTextEdit,
    QPushButton, QCheckBox, QStyleFactory
)
from PyQt6.QtCore import Qt

# --- Constants ---
MARKER = "# MANAGED BY PYQT-BLOCKER"
REDIRECT_IP = "127.0.0.1"

class BlockerApp(QWidget):
    def __init__(self):
        super().__init__()
        self.hosts_path = self.get_hosts_path()
        self.initUI()
        self.load_initial_state()

    def initUI(self):
        """Sets up the application's GUI."""
        self.setWindowTitle('PyQt Website Blocker')
        self.setGeometry(300, 300, 400, 300)
        
        # Use a consistent style
        QApplication.setStyle(QStyleFactory.create('Fusion'))

        # Layout
        layout = QVBoxLayout()

        # --- Widgets ---
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
        
        self.setLayout(layout)

        # --- Connect Signals ---
        self.apply_button.clicked.connect(self.apply_changes)

        self.show()

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
                    is_enabled = True # If we find any of our lines, the blocker is on
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
            # Read all lines, filtering out our old managed lines
            with open(self.hosts_path, 'r') as f:
                lines = [line for line in f if MARKER not in line]

            # If the blocker is enabled, add the new lines
            if is_enabled:
                for site in blacklist:
                    if site.strip():  # Ensure site is not an empty string
                        new_line = f"{REDIRECT_IP}\t{site.strip()}\t{MARKER}\n"
                        lines.append(new_line)

            # Write the modified content back to the file
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

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = BlockerApp()
    sys.exit(app.exec())
