# main.py
import sys
import os
import platform
import json
import atexit
from datetime import datetime
from urllib.parse import urlparse

from PyQt6.QtWidgets import QApplication, QWidget, QStyle, QDialog
from PyQt6.QtCore import Qt, QPoint, QSize, QTimer, QDateTime, QStandardPaths
from PyQt6.QtGui import QIcon, QColor

# Import the Windows registry module only if on Windows
if platform.system() == "Windows":
    import winreg

# Import UI classes from the gui.py file
from gui import Ui_BlockerApp, LoginDialog, RegisterDialog

# --- HELPER FUNCTIONS AND GLOBAL CONSTANTS ---

def recolor_icon(icon: QIcon, color: QColor) -> QIcon:
    """
    Takes a QIcon, extracts its pixmap and mask, and returns a new
    icon filled with the desired color.
    """
    pixmap = icon.pixmap(QSize(256, 256))
    mask = pixmap.mask()
    pixmap.fill(color)
    pixmap.setMask(mask)
    return QIcon(pixmap)

MARKER = "# MANAGED BY PYQT-BLOCKER"
REDIRECT_IP = "127.0.0.1"
WEBSITE_CONFIG_FILE = "blocked_websites.json"
APP_CONFIG_FILE = "blocked_apps.txt"
# Tema escuro da aplicação em formato CSS
DARK_THEME = """
QWidget { background-color: #2b2b2b; color: #f0f0f0; font-family: Segoe UI; font-size: 14px; }
QWidget#title_bar { background-color: #1e1e1e; }
QWidget#nav_bar { background-color: #3c3c3c; border-bottom: 1px solid #555; }
QPushButton#nav_button { background-color: transparent; border: none; padding: 10px; font-size: 15px; font-weight: bold; color: #a9a9a9; }
QPushButton#nav_button:hover { background-color: #4f4f4f; }
QPushButton#nav_button[active="true"] { color: #ffffff; border-bottom: 2px solid #0078d7; }
QLineEdit#time_input { background-color: transparent; border: none; color: #f0f0f0; font-size: 40px; font-weight: bold; max-width: 60px; text-align: center; }
QLabel#time_colon { font-size: 35px; font-weight: bold; color: #f0f0f0; }
QLabel#title_label { font-size: 16px; font-weight: bold; padding-left: 5px; }
QPushButton { background-color: #555555; border: 1px solid #777777; padding: 8px; border-radius: 3px; }
QPushButton:hover { background-color: #6a6a6a; }
QPushButton#start_button { background-color: #0078d7; font-weight: bold; }
QPushButton#reset_button { background-color: #555; font-weight: bold; }
QTextEdit { background-color: #3c3c3c; border: 1px solid #555555; border-radius: 3px; }
QPushButton#minimize_button, QPushButton#maximize_button, QPushButton#close_button { background-color: transparent; border: none; padding: 2px; }
QPushButton#minimize_button:hover, QPushButton#maximize_button:hover { background-color: #555555; }
QPushButton#close_button:hover { background-color: #e81123; }
QTabWidget::pane { border: none; }
QTabBar { qproperty-drawBase: 0; }
QLabel#login_title {
    font-size: 24px;
    font-weight: bold;
    padding-bottom: 15px;
    qproperty-alignment: 'AlignCenter';
}
QPushButton#primary_button {
    background-color: #0078d7;
    font-weight: bold;
}
QPushButton#primary_button:hover {
    background-color: #008ae6;
}
"""

# --- MAIN APPLICATION CLASS ---

class BlockerApp(QWidget):
    """Main application class, handles logic and UI setup."""
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

        # <<< CHANGE START: Reordered this list to match the UI >>>
        self.nav_buttons = [
            self.ui.nav_button_timer,
            self.ui.nav_button_lista,
            self.ui.nav_button_estatisticas,
            self.ui.nav_button_rank,
        ]
        # <<< CHANGE END >>>

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_countdown)
        self.total_seconds = 0
        self.end_time = None

        self.connect_signals()
        self.load_initial_state()
        self.reset_timer()
        self.change_tab(0)

    def cleanup_all_blocks(self):
        """Removes all blocks applied by this session upon closing."""
        print(">>> Initiating cleanup of all blocking rules...")
        self.update_hosts_file([], is_enabled=False, is_cleanup=True)
        if platform.system() == "Windows":
            for exe in list(self.previously_blocked_exes):
                self.unblock_executable(exe)
        print(">>> Cleanup complete.")

    def closeEvent(self, event):
        """Intercepts the window close event to run cleanup."""
        self.cleanup_all_blocks()
        event.accept()

    def _setup_title_bar_icons(self):
        """Gets system icons, recolors them, and applies them to buttons."""
        style = self.style()
        app_icon_color = QColor("#0078d7")
        button_icon_color = QColor("white")
        
        try:
            app_icon = QIcon("icon.png")
            colored_app_icon = recolor_icon(app_icon, app_icon_color)
            self.setWindowIcon(colored_app_icon)
            self.ui.icon_label.setPixmap(colored_app_icon.pixmap(QSize(256, 256)))
        except Exception as e:
            print(f"Could not load or set app icon: {e}. Make sure icon.png is in the same folder.")

        self.ui.minimize_button.setIcon(recolor_icon(style.standardIcon(QStyle.StandardPixmap.SP_TitleBarMinButton), button_icon_color))
        self.ui.maximize_button.setIcon(recolor_icon(style.standardIcon(QStyle.StandardPixmap.SP_TitleBarMaxButton), button_icon_color))
        self.ui.close_button.setIcon(recolor_icon(style.standardIcon(QStyle.StandardPixmap.SP_TitleBarCloseButton), button_icon_color))

        self.ui.minimize_button.setFixedSize(32, 32)
        self.ui.maximize_button.setFixedSize(32, 32)
        self.ui.close_button.setFixedSize(32, 32)

        self.ui.minimize_button.setIconSize(QSize(16, 16))
        self.ui.maximize_button.setIconSize(QSize(16, 16))
        self.ui.close_button.setIconSize(QSize(16, 16))

    def connect_signals(self):
        """Connects widget signals (e.g., clicks) to their functions."""
        self.ui.nav_button_timer.clicked.connect(lambda: self.change_tab(0))
        self.ui.nav_button_lista.clicked.connect(lambda: self.change_tab(1))
        # <<< CHANGE START: Corrected the tab indices for the buttons >>>
        self.ui.nav_button_estatisticas.clicked.connect(lambda: self.change_tab(2))
        self.ui.nav_button_rank.clicked.connect(lambda: self.change_tab(3))
        # <<< CHANGE END >>>

        self.ui.close_button.clicked.connect(self.close)
        self.ui.minimize_button.clicked.connect(self.showMinimized)
        self.ui.maximize_button.clicked.connect(self.toggle_maximize)

        self.ui.apply_button.clicked.connect(self.apply_all_changes)

        self.ui.start_button.clicked.connect(self.start_timer)
        self.ui.reset_button.clicked.connect(self.reset_timer)

        self.ui.add_url_button.clicked.connect(self.add_url_from_input)
        self.ui.remove_url_button.clicked.connect(self.remove_selected_url)
        self.ui.url_input.returnPressed.connect(self.add_url_from_input)

    def add_url_from_input(self):
        """Gets text from the input, validates, and adds it to the visual list."""
        url_text = self.ui.url_input.text().strip()
        if not url_text:
            return

        if not url_text.startswith(('http://', 'https://')):
            url_text = 'http://' + url_text
        try:
            domain = urlparse(url_text).netloc
            if domain.startswith('www.'):
                domain = domain[4:]

            if domain:
                items = [self.ui.website_list_widget.item(i).text() for i in range(self.ui.website_list_widget.count())]
                if domain not in items:
                    self.ui.website_list_widget.addItem(domain)
                    self.ui.url_input.clear()
                else:
                    self.ui.status_label.setText("Status: Domain is already in the list.")
            else:
                self.ui.status_label.setText("Status: Invalid URL.")
        except Exception as e:
            self.ui.status_label.setText(f"Status: Error processing URL - {e}")

    def remove_selected_url(self):
        """Removes the currently selected item from the URL list."""
        list_items = self.ui.website_list_widget.selectedItems()
        if not list_items:
            return
        for item in list_items:
            row = self.ui.website_list_widget.row(item)
            self.ui.website_list_widget.takeItem(row)

    def start_timer(self):
        """Starts the timer and ACTIVATES blocking."""
        hours = int(self.ui.circular_timer.hour_input.text() or 0)
        minutes = int(self.ui.circular_timer.minute_input.text() or 0)
        seconds = int(self.ui.circular_timer.second_input.text() or 0)
        self.total_seconds = (hours * 3600) + (minutes * 60) + seconds

        if self.total_seconds > 0:
            self.ui.enable_checkbox.setChecked(True)
            self.apply_all_changes()
            self.ui.status_label.setText("Status: Focus session started!")
            self.ui.enable_checkbox.setEnabled(False)
            self.ui.apply_button.setEnabled(False)

            self.end_time = QDateTime.currentDateTime().addSecs(self.total_seconds)
            self.timer.start(16)
            self.ui.start_button.setEnabled(False)
            self.ui.circular_timer.set_inputs_visible(False)

    def update_countdown(self):
        """Called by the QTimer to update the remaining time."""
        now = QDateTime.currentDateTime()
        remaining_msecs = now.msecsTo(self.end_time)

        if remaining_msecs <= 0:
            # Envia a duração total do timer para o servidor quando o tempo acaba.
            self.send_block_time_to_server(self.total_seconds)
            updated_data = self.save_session_history(self.total_seconds)
            self.ui.history_graph.load_history(updated_data)
            self.timer.stop()
            self.ui.status_label.setText("Status: Timer finished! Sites unblocked.")
            QApplication.beep()
            self.reset_timer()
            return

        current_seconds_float = remaining_msecs / 1000.0
        self.ui.circular_timer.set_time(self.total_seconds, current_seconds_float)

    def reset_timer(self):
        """Stops and resets the timer, and DEACTIVATES blocking."""
        self.timer.stop()
        h = int(self.ui.circular_timer.hour_input.text() or 0)
        m = int(self.ui.circular_timer.minute_input.text() or 0)
        s = int(self.ui.circular_timer.second_input.text() or 0)
        self.total_seconds = (h * 3600) + (m * 60) + s

        self.ui.enable_checkbox.setChecked(False)
        self.apply_all_changes()
        self.ui.status_label.setText("Status: Ready to start.")
        self.ui.enable_checkbox.setEnabled(True)
        self.ui.apply_button.setEnabled(True)

        self.ui.circular_timer.set_time(self.total_seconds, self.total_seconds)
        self.ui.start_button.setEnabled(True)
        self.ui.circular_timer.set_inputs_visible(True)

    def change_tab(self, index):
        """Changes the visible tab and updates navigation button styles."""
        self.ui.tabs.setCurrentIndex(index)
        for i, button in enumerate(self.nav_buttons):
            button.setProperty("active", i == index)
            button.style().polish(button)
            
    ### MODIFICADO: apply_all_changes agora também salva as listas ###
    def apply_all_changes(self):
        is_enabled = self.ui.enable_checkbox.isChecked()
        website_list = [self.ui.website_list_widget.item(i).text() for i in range(self.ui.website_list_widget.count())]
        self.update_hosts_file(website_list, is_enabled)

        if platform.system() == "Windows":
             self.update_exe_blocks(self.ui.app_list_edit.toPlainText().split('\n'), is_enabled)
        
        # Salva as listas nos arquivos de configuração após aplicar
        self.save_lists_to_files()

    ### MODIFICADO: load_initial_state agora carrega as listas salvas ###
    def load_initial_state(self):
        self.cleanup_all_blocks()
        self.load_lists_from_files() # Carrega as listas salvas para a UI
        self.ui.status_label.setText("Status: Pronto. Listas anteriores carregadas.")

        app_data_path = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation)
        history_file = os.path.join(app_data_path, "blocker_history.json")
        try:
            with open(history_file, 'r') as f: history_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            history_data = {}
        self.ui.history_graph.load_history(history_data)
    ### NOVAS FUNÇÕES PARA SALVAR E CARREGAR LISTAS ###
    def get_config_path(self, filename):
        """Retorna o caminho completo para um arquivo de configuração na pasta AppData."""
        app_data_path = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation)
        # Cria o diretório se ele não existir
        os.makedirs(app_data_path, exist_ok=True)
        return os.path.join(app_data_path, filename)

    def save_lists_to_files(self):
        """Salva as listas de bloqueio em arquivos na pasta AppData."""
        try:
            # Salva a lista de websites (JSON, pois vem de um QListWidget)
            websites_path = self.get_config_path(WEBSITE_CONFIG_FILE)
            website_list = [self.ui.website_list_widget.item(i).text() for i in range(self.ui.website_list_widget.count())]
            with open(websites_path, 'w') as f:
                json.dump(website_list, f)

            # Salva a lista de apps (TXT, pois vem de um QTextEdit)
            if platform.system() == "Windows":
                apps_path = self.get_config_path(APP_CONFIG_FILE)
                with open(apps_path, 'w') as f:
                    f.write(self.ui.app_list_edit.toPlainText())
            
            print(">>> Listas de bloqueio salvas.")
        except Exception as e:
            print(f"Erro ao salvar listas de configuração: {e}")

    def load_lists_from_files(self):
        """Carrega as listas de bloqueio dos arquivos na pasta AppData."""
        try:
            # Carrega a lista de websites
            websites_path = self.get_config_path(WEBSITE_CONFIG_FILE)
            if os.path.exists(websites_path):
                with open(websites_path, 'r') as f:
                    website_list = json.load(f)
                    self.ui.website_list_widget.clear()
                    self.ui.website_list_widget.addItems(website_list)

            # Carrega a lista de apps
            if platform.system() == "Windows":
                apps_path = self.get_config_path(APP_CONFIG_FILE)
                if os.path.exists(apps_path):
                    with open(apps_path, 'r') as f:
                        self.ui.app_list_edit.setText(f.read())
            
            print(">>> Listas de bloqueio carregadas.")
        except Exception as e:
            print(f"Erro ao carregar listas de configuração: {e}")
    
    def save_session_history(self, session_duration_seconds):
        """Reads, updates, and saves the session history to a JSON file."""
        app_data_path = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation)
        os.makedirs(app_data_path, exist_ok=True)
        history_file = os.path.join(app_data_path, "blocker_history.json")

        today_str = datetime.now().strftime("%Y-%m-%d")

        data = {}
        try:
            with open(history_file, 'r') as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            pass

        data[today_str] = data.get(today_str, 0) + session_duration_seconds

        with open(history_file, 'w') as f:
            json.dump(data, f)
        
        return data

    def update_hosts_file(self, blacklist, is_enabled, is_cleanup=False):
        """Updates the hosts file with the list of URLs to block."""
        try:
            with open(self.hosts_path, 'r') as f:
                lines = [line for line in f if MARKER not in line]

            if is_enabled:
                for site in blacklist:
                    if site.strip():
                        lines.append(f"{REDIRECT_IP}\t{site.strip()}\t{MARKER}\n")

            with open(self.hosts_path, 'w') as f:
                f.writelines(lines)

            if not is_cleanup and is_enabled:
                self.ui.status_label.setText("Status: Block list updated!")
                self.ui.status_label.setStyleSheet("color: #55ff7f;")
                self.flush_dns()
        except PermissionError:
             self.ui.status_label.setText("Hosts Error: Permission denied. Run as Administrator.")
             self.ui.status_label.setStyleSheet("color: #ff5555;")
        except Exception as e:
            self.ui.status_label.setText(f"Hosts Error: {e}")
            self.ui.status_label.setStyleSheet("color: #ff5555;")

    def update_exe_blocks(self, blacklist, is_enabled):
        """Updates the Windows Registry to block/unblock executables."""
        try:
            current_blacklist = {exe.strip().lower() for exe in blacklist if exe.strip()}
            to_unblock = self.previously_blocked_exes - current_blacklist
            for exe in to_unblock:
                self.unblock_executable(exe)

            if is_enabled:
                to_block = current_blacklist
                for exe in to_block:
                    self.block_executable(exe)
            else:
                to_block = set()
                for exe in self.previously_blocked_exes:
                    self.unblock_executable(exe)

            self.previously_blocked_exes = to_block if is_enabled else set()

            if not self.ui.website_list_widget.count() > 0 and is_enabled:
                 self.ui.status_label.setText("Status: Block list updated!")
                 self.ui.status_label.setStyleSheet("color: #55ff7f;")
        except PermissionError:
             self.ui.status_label.setText("App Block Error: Permission denied. Run as Admin.")
             self.ui.status_label.setStyleSheet("color: #ff5555;")
        except Exception as e:
            self.ui.status_label.setText(f"App Block Error: {e}")
            self.ui.status_label.setStyleSheet("color: #ff5555;")

    def load_exe_block_state(self):
        """Loads currently blocked EXEs from the registry on startup."""
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
                    except OSError:
                        break
            self.ui.app_list_edit.setText('\n'.join(sorted(list(blocked_exes))))
            self.previously_blocked_exes = blocked_exes
        except FileNotFoundError:
            pass
        except Exception as e:
            print(f"Could not load EXE state: {e}")

    def block_executable(self, exe_name):
        """Creates a registry key to intercept an .exe's execution."""
        try:
            key_path = fr"Software\Microsoft\Windows NT\CurrentVersion\Image File Execution Options\{exe_name}"
            with winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, key_path) as key:
                debugger_command = f'"{sys.executable}" "{self.helper_path}"'
                winreg.SetValueEx(key, "Debugger", 0, winreg.REG_SZ, debugger_command)
        except Exception as e:
            print(f"Error blocking {exe_name}: {e}")

    def unblock_executable(self, exe_name):
        """Removes the registry key that blocks an .exe's execution."""
        try:
            key_path = fr"Software\Microsoft\Windows NT\CurrentVersion\Image File Execution Options\{exe_name}"
            winreg.DeleteKey(winreg.HKEY_LOCAL_MACHINE, key_path)
            self.previously_blocked_exes.discard(exe_name)
        except FileNotFoundError:
            pass
        except Exception as e:
            print(f"Error unblocking {exe_name}: {e}")

    def flush_dns(self):
        """Flushes the operating system's DNS cache."""
        os_name = platform.system()
        if os_name == "Windows":
            os.system("ipconfig /flushdns > NUL 2>&1")
        elif os_name == "Linux":
            print(">>> Flushing Linux DNS cache...")
            os.system("sudo systemd-resolve --flush-caches")
            print(">>> DNS cache flushed.")

    def get_hosts_path(self):
        """Returns the hosts file path depending on the OS."""
        if platform.system() == "Windows":
            return r"C:\Windows\System32\drivers\etc\hosts"
        else:
            return "/etc/hosts"

    def get_helper_path(self):
        """Returns the absolute path to the blocker helper script."""
        script_dir = os.path.dirname(__file__)
        return os.path.abspath(os.path.join(script_dir, 'blocker_helper.pyw'))

    def toggle_maximize(self):
        """Toggles the window between maximized and normal states."""
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    def mousePressEvent(self, event):
        """Captures the mouse click on the title bar to initiate a drag."""
        if event.button() == Qt.MouseButton.LeftButton and self.ui.title_bar.underMouse():
            self.old_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        """Moves the window if the mouse is being dragged."""
        if self.old_pos:
            delta = QPoint(event.globalPosition().toPoint() - self.old_pos)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event):
        """Finalizes the window drag when the mouse is released."""
        self.old_pos = None

    def send_block_time_to_server(self, duration_seconds):
        """Envia a duração da sessão de bloqueio para o servidor."""
        if not hasattr(self, 'logged_in_user') or not self.logged_in_user:
            return # Não faz nada se não houver usuário logado

        server_url = f"{SERVER_BASE_URL}/add_time"
        payload = {
            'username': self.logged_in_user,
            'seconds': duration_seconds
        }

        try:
            requests.post(server_url, json=payload, timeout=10)
            print(f">>> Tempo de bloqueio ({duration_seconds}s) enviado para o servidor para o usuário {self.logged_in_user}.")
        except requests.exceptions.RequestException as e:
            print(f"*** ERRO ao enviar tempo para o servidor: {e}")

# --- PONTO DE ENTRADA DA APLICAÇÃO ---
if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyleSheet(DARK_THEME)

    login_dialog = LoginDialog()
    if login_dialog.exec() == QDialog.DialogCode.Accepted:
        main_app = BlockerApp()
        atexit.register(main_app.cleanup_all_blocks)
        main_app.show()
        sys.exit(app.exec())
    else:
        sys.exit(0)