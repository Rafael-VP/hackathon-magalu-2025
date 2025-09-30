# main.py
import sys
import os
import platform
from PyQt6.QtWidgets import QApplication, QWidget, QStyle, QLabel
from PyQt6.QtCore import Qt, QPoint, QSize
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor

if platform.system() == "Windows":
    import winreg

from gui import Ui_BlockerApp

def recolor_icon(icon: QIcon, color: QColor) -> QIcon:
    pixmap = icon.pixmap(QSize(256, 256))
    mask = pixmap.mask()
    pixmap.fill(color)
    pixmap.setMask(mask)
    return QIcon(pixmap)

MARKER = "# MANAGED BY PYQT-BLOCKER"
REDIRECT_IP = "127.0.0.1"
DARK_THEME = """
QWidget {
    background-color: #2b2b2b; color: #f0f0f0;
    font-family: Segoe UI; font-size: 14px;
}
QWidget#title_bar { background-color: #1e1e1e; }
QWidget#nav_bar { background-color: #3c3c3c; border-bottom: 1px solid #555; }

/* Estilo dos botões de navegação */
QPushButton#nav_button {
    background-color: transparent; border: none; padding: 10px;
    font-size: 15px; font-weight: bold; color: #a9a9a9;
}
QPushButton#nav_button:hover { background-color: #4f4f4f; }
QPushButton#nav_button[active="true"] {
    color: #ffffff; border-bottom: 2px solid #0078d7;
}

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
    background-color: transparent; border: none; padding: 2px;
}
QPushButton#minimize_button:hover, QPushButton#maximize_button:hover { background-color: #555555; }
QPushButton#close_button:hover { background-color: #e81123; }
QTabWidget::pane { border: none; }
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
        
        self._setup_title_bar_icons()
        
        self.old_pos = None
        self.hosts_path = self.get_hosts_path()
        if platform.system() == "Windows":
            self.helper_path = self.get_helper_path()
            self.previously_blocked_exes = set()
        
        # --- INÍCIO DA MODIFICAÇÃO: LISTA DE 5 BOTÕES ---
        self.nav_buttons = [
            self.ui.nav_button_timer,
            self.ui.nav_button_lista,
            self.ui.nav_button_rank,
            self.ui.nav_button_estatisticas,
            self.ui.nav_button_graficos
        ]
        # --- FIM DA MODIFICAÇÃO ---
        
        self.connect_signals()
        self.load_initial_state()
        self.change_tab(0)
        self.show()

    def _setup_title_bar_icons(self):
        style = self.style()
        icon_color = QColor("white")
        
        self.ui.minimize_button.setIcon(recolor_icon(style.standardIcon(QStyle.StandardPixmap.SP_TitleBarMinButton), icon_color))
        self.ui.maximize_button.setIcon(recolor_icon(style.standardIcon(QStyle.StandardPixmap.SP_TitleBarMaxButton), icon_color))
        self.ui.close_button.setIcon(recolor_icon(style.standardIcon(QStyle.StandardPixmap.SP_TitleBarCloseButton), icon_color))
        
        self.ui.minimize_button.setFixedSize(32, 32)
        self.ui.maximize_button.setFixedSize(32, 32)
        self.ui.close_button.setFixedSize(32, 32)
        self.ui.minimize_button.setIconSize(QSize(16, 16))
        self.ui.maximize_button.setIconSize(QSize(16, 16))
        self.ui.close_button.setIconSize(QSize(16, 16))

    def connect_signals(self):
        self.apply_button.clicked.connect(self.apply_all_changes)
        
        # --- INÍCIO DA MODIFICAÇÃO: CONEXÃO DOS 5 BOTÕES ---
        self.ui.nav_button_timer.clicked.connect(lambda: self.change_tab(0))
        self.ui.nav_button_lista.clicked.connect(lambda: self.change_tab(1))
        self.ui.nav_button_rank.clicked.connect(lambda: self.change_tab(2))
        self.ui.nav_button_estatisticas.clicked.connect(lambda: self.change_tab(3))
        self.ui.nav_button_graficos.clicked.connect(lambda: self.change_tab(4))
        # --- FIM DA MODIFICAÇÃO ---

        # Conexões dos botões da janela
        self.ui.close_button.clicked.connect(self.close)
        self.ui.minimize_button.clicked.connect(self.showMinimized)
        self.ui.maximize_button.clicked.connect(self.toggle_maximize)

    def change_tab(self, index):
        """Muda a aba visível e atualiza o estilo dos botões de navegação."""
        self.ui.tabs.setCurrentIndex(index)
        for i, button in enumerate(self.nav_buttons):
            button.setProperty("active", i == index)
            button.style().polish(button)

    # --- O resto do arquivo (lógica de bloqueio) permanece o mesmo ---
    def apply_all_changes(self):
        is_enabled = self.enable_checkbox.isChecked()
        self.update_hosts_file(self.website_list_edit.toPlainText().split('\n'), is_enabled)
        if platform.system() == "Windows":
            self.update_exe_blocks(self.app_list_edit.toPlainText().split('\n'), is_enabled)

    def load_initial_state(self):
        try:
            with open(self.hosts_path, 'r') as f: lines = f.readlines()
            blocked_sites, is_enabled = [], False
            for line in lines:
                if MARKER in line:
                    is_enabled = True
                    parts = line.split()
                    if len(parts) >= 2: blocked_sites.append(parts[1])
            self.website_list_edit.setText('\n'.join(blocked_sites))
            self.enable_checkbox.setChecked(is_enabled)
            self.status_label.setText("Status: Loaded hosts file.")
        except Exception:
            self.status_label.setText(f"Status: Error loading hosts file.")
        if platform.system() == "Windows": self.load_exe_block_state()

    def update_hosts_file(self, blacklist, is_enabled):
        try:
            with open(self.hosts_path, 'r') as f: lines = [line for line in f if MARKER not in line]
            if is_enabled:
                for site in blacklist:
                    if site.strip(): lines.append(f"{REDIRECT_IP}\t{site.strip()}\t{MARKER}\n")
            with open(self.hosts_path, 'w') as f: f.writelines(lines)
            self.status_label.setText("Status: Hosts file updated!")
            self.status_label.setStyleSheet("color: green;")
            self.flush_dns()
        except Exception as e:
            self.status_label.setText(f"Hosts Error: {e}. Run as Admin.")
            self.status_label.setStyleSheet("color: red;")

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
                            if self.helper_path in debugger_val: blocked_exes.add(exe_name)
                        i += 1
                    except OSError: break
            self.app_list_edit.setText('\n'.join(sorted(list(blocked_exes))))
            self.previously_blocked_exes = blocked_exes
        except FileNotFoundError: pass
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

    def get_hosts_path(self): return r"C:\Windows\System32\drivers\etc\hosts" if platform.system() == "Windows" else "/etc/hosts"
    def get_helper_path(self): return os.path.abspath(os.path.join(os.path.dirname(__file__), 'blocker_helper.pyw'))
    def flush_dns(self):
        if platform.system() == "Windows": os.system("ipconfig /flushdns")
    def toggle_maximize(self):
        if self.isMaximized(): self.showNormal()
        else: self.showMaximized()
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.ui.title_bar.underMouse(): self.old_pos = event.globalPosition().toPoint()
    def mouseMoveEvent(self, event):
        if self.old_pos: delta = QPoint(event.globalPosition().toPoint() - self.old_pos); self.move(self.x() + delta.x(), self.y() + delta.y()); self.old_pos = event.globalPosition().toPoint()
    def mouseReleaseEvent(self, event): self.old_pos = None

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyleSheet(DARK_THEME)
    ex = BlockerApp()
    sys.exit(app.exec())