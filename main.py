# main.py
import sys
import os
import platform
from PyQt6.QtWidgets import QApplication, QWidget, QStyle
from PyQt6.QtCore import Qt, QPoint, QSize, QTimer, QDateTime
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor

if platform.system() == "Windows":
    import winreg

from gui import Ui_BlockerApp

def recolor_icon(icon: QIcon, color: QColor) -> QIcon:
    pixmap = icon.pixmap(QSize(256, 256)); mask = pixmap.mask(); pixmap.fill(color); pixmap.setMask(mask)
    return QIcon(pixmap)

MARKER = "# MANAGED BY PYQT-BLOCKER"
REDIRECT_IP = "127.0.0.1"
DARK_THEME = """
QWidget { background-color: #2b2b2b; color: #f0f0f0; font-family: Segoe UI; font-size: 14px; }
QWidget#title_bar { background-color: #1e1e1e; }
QWidget#nav_bar { background-color: #3c3c3c; border-bottom: 1px solid #555; }
QPushButton#nav_button {
    background-color: transparent; border: none; padding: 10px; font-size: 15px; font-weight: bold; color: #a9a9a9;
}
QPushButton#nav_button:hover { background-color: #4f4f4f; }
QPushButton#nav_button[active="true"] { color: #ffffff; border-bottom: 2px solid #0078d7; }
QLineEdit#time_input {
    background-color: transparent; border: none; color: #f0f0f0; font-size: 40px; font-weight: bold;
    max-width: 60px; text-align: center;
}
QLabel#time_colon { font-size: 35px; font-weight: bold; color: #f0f0f0; }
QLabel#title_label { font-size: 16px; font-weight: bold; padding-left: 5px; }
QPushButton { background-color: #555555; border: 1px solid #777777; padding: 8px; border-radius: 3px; }
QPushButton:hover { background-color: #6a6a6a; }
QPushButton#start_button { background-color: #0078d7; }
QPushButton#reset_button { background-color: #555; }
QTextEdit { background-color: #3c3c3c; border: 1px solid #555555; border-radius: 3px; }
QPushButton#minimize_button, QPushButton#maximize_button, QPushButton#close_button { background-color: transparent; border: none; padding: 2px; }
QPushButton#minimize_button:hover, QPushButton#maximize_button:hover { background-color: #555555; }
QPushButton#close_button:hover { background-color: #e81123; }
QTabWidget::pane { border: none; }
QTabBar::tab { border: none; }
"""

class BlockerApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.ui = Ui_BlockerApp()
        self.ui.setupUi(self)
        self._setup_title_bar_icons()
        self.old_pos = None; self.hosts_path = self.get_hosts_path()
        if platform.system() == "Windows": self.helper_path = self.get_helper_path(); self.previously_blocked_exes = set()
        
        # --- LISTA DE BOTÕES RESTAURADA ---
        self.nav_buttons = [
            self.ui.nav_button_timer,
            self.ui.nav_button_lista,
            self.ui.nav_button_rank,
            self.ui.nav_button_estatisticas,
            self.ui.nav_button_graficos
        ]
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_countdown)
        self.total_seconds = 0; self.end_time = None
        
        self.connect_signals()
        self.load_initial_state()
        self.reset_timer()
        self.change_tab(0)
        self.show()

    def _setup_title_bar_icons(self):
        style = self.style(); icon_color = QColor("white")
        self.ui.minimize_button.setIcon(recolor_icon(style.standardIcon(QStyle.StandardPixmap.SP_TitleBarMinButton), icon_color))
        self.ui.maximize_button.setIcon(recolor_icon(style.standardIcon(QStyle.StandardPixmap.SP_TitleBarMaxButton), icon_color))
        self.ui.close_button.setIcon(recolor_icon(style.standardIcon(QStyle.StandardPixmap.SP_TitleBarCloseButton), icon_color))
        self.ui.minimize_button.setFixedSize(32, 32); self.ui.maximize_button.setFixedSize(32, 32); self.ui.close_button.setFixedSize(32, 32)
        self.ui.minimize_button.setIconSize(QSize(16, 16)); self.ui.maximize_button.setIconSize(QSize(16, 16)); self.ui.close_button.setIconSize(QSize(16, 16))

    def connect_signals(self):
        # Sinais de navegação
        self.ui.nav_button_timer.clicked.connect(lambda: self.change_tab(0))
        self.ui.nav_button_lista.clicked.connect(lambda: self.change_tab(1))
        # --- SINAIS RESTAURADOS ---
        self.ui.nav_button_rank.clicked.connect(lambda: self.change_tab(2))
        self.ui.nav_button_estatisticas.clicked.connect(lambda: self.change_tab(3))
        self.ui.nav_button_graficos.clicked.connect(lambda: self.change_tab(4))
        
        # Sinais da janela
        self.ui.close_button.clicked.connect(self.close)
        self.ui.minimize_button.clicked.connect(self.showMinimized)
        self.ui.maximize_button.clicked.connect(self.toggle_maximize)
        # Sinais do Blocker
        self.apply_button.clicked.connect(self.apply_all_changes)
        # Sinais do Timer
        self.start_button.clicked.connect(self.start_timer)
        self.reset_button.clicked.connect(self.reset_timer)

    def start_timer(self):
        hours = int(self.circular_timer.hour_input.text() or 0)
        minutes = int(self.circular_timer.minute_input.text() or 0)
        seconds = int(self.circular_timer.second_input.text() or 0)
        self.total_seconds = (hours * 3600) + (minutes * 60) + seconds
        if self.total_seconds > 0:
            self.end_time = QDateTime.currentDateTime().addSecs(self.total_seconds)
            self.timer.start(16)
            self.start_button.setEnabled(False)
            self.circular_timer.set_inputs_visible(False)

    def update_countdown(self):
        now = QDateTime.currentDateTime()
        remaining_msecs = now.msecsTo(self.end_time)
        if remaining_msecs <= 0:
            self.timer.stop(); self.status_label.setText("Status: Timer finished!"); QApplication.beep(); self.reset_timer()
            return
        current_seconds_float = remaining_msecs / 1000.0
        self.circular_timer.set_time(self.total_seconds, current_seconds_float)

    def reset_timer(self):
        self.timer.stop()
        h = int(self.circular_timer.hour_input.text() or 0); m = int(self.circular_timer.minute_input.text() or 0); s = int(self.circular_timer.second_input.text() or 0)
        self.total_seconds = (h * 3600) + (m * 60) + s
        self.circular_timer.set_time(self.total_seconds, self.total_seconds)
        self.start_button.setEnabled(True)
        self.circular_timer.set_inputs_visible(True)

    def change_tab(self, index):
        self.ui.tabs.setCurrentIndex(index)
        for i, button in enumerate(self.nav_buttons):
            button.setProperty("active", i == index); button.style().polish(button)
            
    def apply_all_changes(self):
        is_enabled = self.enable_checkbox.isChecked()
        if platform.system() == "Windows": self.update_exe_blocks(self.app_list_edit.toPlainText().split('\n'), is_enabled)
    def load_initial_state(self):
        if platform.system() == "Windows": self.load_exe_block_state()
    def update_exe_blocks(self, blacklist, is_enabled):
        try:
            current_blacklist = {exe.strip() for exe in blacklist if exe.strip()}
            to_unblock = self.previously_blocked_exes - current_blacklist
            for exe in to_unblock: self.unblock_executable(exe)
            if is_enabled:
                to_block = current_blacklist
                for exe in to_block: self.block_executable(exe)
            else:
                to_block = set();
                for exe in self.previously_blocked_exes: self.unblock_executable(exe)
            self.previously_blocked_exes = to_block if is_enabled else set()
            self.status_label.setText("Status: App block list updated!"); self.status_label.setStyleSheet("color: green;")
        except Exception as e:
            self.status_label.setText(f"App Block Error: {e}. Run as Admin."); self.status_label.setStyleSheet("color: red;")
    def load_exe_block_state(self):
        key_path = r"Software\Microsoft\Windows NT\CurrentVersion\Image File Execution Options"; blocked_exes = set()
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
    def block_executable(self, exe_name):
        try:
            key_path = fr"Software\Microsoft\Windows NT\CurrentVersion\Image File Execution Options\{exe_name}"
            with winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, key_path) as key:
                debugger_command = f'"{sys.executable}" "{self.helper_path}"'; winreg.SetValueEx(key, "Debugger", 0, winreg.REG_SZ, debugger_command)
        except Exception as e: print(f"Error blocking {exe_name}: {e}")
    def unblock_executable(self, exe_name):
        try:
            key_path = fr"Software\Microsoft\Windows NT\CurrentVersion\Image File Execution Options\{exe_name}"
            winreg.DeleteKey(winreg.HKEY_LOCAL_MACHINE, key_path)
        except Exception as e: print(f"Error unblocking {exe_name}: {e}")
    def get_hosts_path(self): return r"C:\Windows\System32\drivers\etc\hosts" if platform.system() == "Windows" else "/etc/hosts"
    def get_helper_path(self): return os.path.abspath(os.path.join(os.path.dirname(__file__), 'blocker_helper.pyw'))
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