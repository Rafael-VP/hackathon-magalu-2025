# main.py
import sys
import os
import requests
import platform
import json
import atexit
from datetime import datetime
from urllib.parse import urlparse
from PyQt6.QtWidgets import (QApplication, QWidget, QStyle, QDialog, QLineEdit,
                             QPushButton, QLabel, QFormLayout, QHBoxLayout, QVBoxLayout)
from PyQt6.QtCore import Qt, QPoint, QSize, QTimer, QDateTime, QStandardPaths
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtGui import QIcon, QColor, QPixmap, QPainter

if platform.system() == "Windows":
    import winreg

# Importa a classe da interface do usuário do arquivo gui.py
from gui import Ui_BlockerApp, LoginDialog, RegisterDialog, recolor_icon

# --- FUNÇÕES AUXILIARES E CONSTANTES GLOBAIS ---

def recolor_svg_to_pixmap(svg_path: str, color: QColor, size: QSize) -> QPixmap:

    try:
        with open(svg_path, "r") as f:
            svg_data = f.read()
        
        # IMPORTANT: Your SVG file must use fill="#000000" for the parts you want to color.
        colored_svg_data = svg_data.replace('fill="#000000"', f'fill="{color.name()}"')
        
        pixmap = QPixmap(size)
        pixmap.fill(Qt.GlobalColor.transparent)
        renderer = QSvgRenderer(bytearray(colored_svg_data, 'utf-8'))
        
        painter = QPainter(pixmap)
        renderer.render(painter)
        painter.end()
        
        return pixmap
    except Exception as e:
        print(f"Error recoloring SVG {svg_path}: {e}")
        return QPixmap() # Return empty pixmap on error

MARKER = "# MANAGED BY PYQT-BLOCKER"
SERVER_BASE_URL = "http://201.23.72.236:5000"
REDIRECT_IP = "127.0.0.1"
SERVER_BASE_URL = "http://201.23.72.236:5000"
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
QLabel#login_title { font-size: 24px; font-weight: bold; padding-bottom: 15px; qproperty-alignment: 'AlignCenter'; }
QPushButton#primary_button { background-color: #0078d7; font-weight: bold; }
QPushButton#primary_button:hover { background-color: #008ae6; }
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
"""

# --- CLASSE PRINCIPAL DA APLICAÇÃO ---

class BlockerApp(QWidget):
    def __init__(self, username: str):
        super().__init__()
        # Armazena o usuário logado para uso futuro
        self.logged_in_user = username
        
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.ui = Ui_BlockerApp()
        self.ui.setupUi(self)

        # Atualiza o título para mostrar quem está logado
        self.ui.title_label.setText(f"hourClass - Usuário: {self.logged_in_user}")
        
        self._setup_title_bar_icons()
        self.old_pos = None
        self.hosts_path = self.get_hosts_path()
        if platform.system() == "Windows":
            self.helper_path = self.get_helper_path()
            self.previously_blocked_exes = set()
        self.nav_buttons = [
            self.ui.nav_button_timer,
            self.ui.nav_button_lista,
            self.ui.nav_button_estatisticas,
            self.ui.nav_button_rank,
        ]
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_countdown)
        self.total_seconds = 0
        self.end_time = None
        self.connect_signals()
        self.load_initial_state()
        self.reset_timer()
        self.change_tab(0)

    def cleanup_all_blocks(self):
        print(">>> Iniciando limpeza de todas as regras de bloqueio...")
        self.update_hosts_file([], is_enabled=False, is_cleanup=True)
        if platform.system() == "Windows":
            for exe in list(self.previously_blocked_exes):
                self.unblock_executable(exe)
        print(">>> Limpeza concluída.")

    def closeEvent(self, event):
        self.cleanup_all_blocks()
        event.accept()

    # main.py -> inside BlockerApp class

    def _setup_title_bar_icons(self):
        """Gets system icons, recolors them, and applies them to buttons."""
        style = self.style()
        app_icon_color = QColor("#0078d7") # Define the color for the app icon
        button_icon_color = QColor("white") # Define the color for the button icons
        
        # This part for the window control buttons remains the same
        self.ui.minimize_button.setIcon(recolor_icon(style.standardIcon(QStyle.StandardPixmap.SP_TitleBarMinButton), button_icon_color))
        self.ui.maximize_button.setIcon(recolor_icon(style.standardIcon(QStyle.StandardPixmap.SP_TitleBarMaxButton), button_icon_color))
        self.ui.close_button.setIcon(recolor_icon(style.standardIcon(QStyle.StandardPixmap.SP_TitleBarCloseButton), button_icon_color))

        # <<< CHANGE: Load, color, and set the main application SVG icon >>>
        try:
            # Use the new function and path
            colored_pixmap = recolor_svg_to_pixmap("data/icon.svg", app_icon_color, QSize(256, 256))
            
            # Set the icon for the main window (taskbar)
            self.setWindowIcon(QIcon(colored_pixmap))
            
            # Set the icon for the label in the title bar
            self.ui.icon_label.setPixmap(colored_pixmap)
        except Exception as e:
            print(f"Could not load or set app icon: {e}")

        # The rest of the method for setting button sizes and icon sizes...
        self.ui.minimize_button.setFixedSize(32, 32)
        self.ui.maximize_button.setFixedSize(32, 32)
        self.ui.close_button.setFixedSize(32, 32)
        
        self.ui.minimize_button.setIconSize(QSize(16, 16))
        self.ui.maximize_button.setIconSize(QSize(16, 16))
        self.ui.close_button.setIconSize(QSize(16, 16))

    def connect_signals(self):
        self.ui.nav_button_timer.clicked.connect(lambda: self.change_tab(0))
        self.ui.nav_button_lista.clicked.connect(lambda: self.change_tab(1))
        self.ui.nav_button_estatisticas.clicked.connect(lambda: self.change_tab(2))
        self.ui.nav_button_rank.clicked.connect(lambda: self.change_tab(3))
        #self.ui.nav_button_graficos.clicked.connect(lambda: self.change_tab(4))
        
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
        url_text = self.ui.url_input.text().strip()
        if not url_text: return
        if not url_text.startswith(('http://', 'https://')): url_text = 'http://' + url_text
        try:
            domain = urlparse(url_text).netloc
            canonical_domain = domain[4:] if domain.startswith('www.') else domain
            if canonical_domain:
                items = [self.ui.website_list_widget.item(i).text() for i in range(self.ui.website_list_widget.count())]
                if canonical_domain not in items:
                    self.ui.website_list_widget.addItem(canonical_domain)
                    self.ui.url_input.clear()
                    self.ui.status_label.setText(f"Status: Domínio '{canonical_domain}' adicionado.")
                else: self.ui.status_label.setText("Status: Domínio já está na lista.")
            else: self.ui.status_label.setText("Status: URL inválida.")
        except Exception as e: self.ui.status_label.setText(f"Status: Erro ao processar URL - {e}")

    def remove_selected_url(self):
        list_items = self.ui.website_list_widget.selectedItems()
        if not list_items: return
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
            # Enable blocking and apply the changes
            self.ui.enable_checkbox.setChecked(True)
            self.apply_all_changes()
            self.ui.status_label.setText("Status: Focus session started!")
            self.ui.enable_checkbox.setEnabled(False)
            self.ui.apply_button.setEnabled(False)

            self.end_time = QDateTime.currentDateTime().addSecs(self.total_seconds)
            self.timer.start(16); self.ui.start_button.setEnabled(False); self.ui.circular_timer.set_inputs_visible(False)

    def update_countdown(self):
        now = QDateTime.currentDateTime()
        remaining_msecs = now.msecsTo(self.end_time)
        if remaining_msecs <= 0:
            # --- ATUALIZADO: Envia o tempo para o servidor ---
            self.send_block_time_to_server(self.total_seconds)
            
            updated_data = self.save_session_history(self.total_seconds)
            self.ui.history_graph.load_history(updated_data)
            self.timer.stop()
            self.ui.status_label.setText("Status: Timer finalizado!")
            QApplication.beep()
            self.reset_timer()
            return
        current_seconds_float = remaining_msecs / 1000.0
        self.ui.circular_timer.set_time(self.total_seconds, current_seconds_float)

    def reset_timer(self):
        """Stops and resets the timer, and DEACTIVATES blocking."""
        self.timer.stop()
        
        # Disable blocking and apply the changes
        self.ui.enable_checkbox.setChecked(False)
        self.apply_all_changes()
        self.ui.status_label.setText("Status: Ready to start.")
        self.ui.enable_checkbox.setEnabled(True)
        self.ui.apply_button.setEnabled(True)

        h = int(self.ui.circular_timer.hour_input.text() or 0)
        m = int(self.ui.circular_timer.minute_input.text() or 0)
        s = int(self.ui.circular_timer.second_input.text() or 0)
        self.total_seconds = (h * 3600) + (m * 60) + s

        self.ui.circular_timer.set_time(self.total_seconds, self.total_seconds)
        self.ui.start_button.setEnabled(True)
        self.ui.circular_timer.set_inputs_visible(True)

    def change_tab(self, index):
        self.ui.tabs.setCurrentIndex(index)
        for i, button in enumerate(self.nav_buttons):
            button.setProperty("active", i == index)
            button.style().polish(button)
            
    def apply_all_changes(self):
        is_enabled = self.ui.enable_checkbox.isChecked()
        website_list = [self.ui.website_list_widget.item(i).text() for i in range(self.ui.website_list_widget.count())]
        self.update_hosts_file(website_list, is_enabled)
        if platform.system() == "Windows":
            self.update_exe_blocks(self.ui.app_list_edit.toPlainText().split('\n'), is_enabled)

    def load_initial_state(self):
        self.cleanup_all_blocks()
        self.ui.status_label.setText("Status: Pronto para iniciar.")
        self.ui.website_list_widget.clear()
        if platform.system() == "Windows":
            self.ui.app_list_edit.setText("")
            self.load_exe_block_state()

        app_data_path = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation)
        history_file = os.path.join(app_data_path, "blocker_history.json")
        try:
            with open(history_file, 'r') as f:
                history_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            history_data = {}
        self.ui.history_graph.load_history(history_data)

    def get_config_path(self, filename):
        app_data_path = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation)
        os.makedirs(app_data_path, exist_ok=True)
        return os.path.join(app_data_path, filename)
    def save_lists_to_files(self):
        try:
            websites_path = self.get_config_path(WEBSITE_CONFIG_FILE)
            website_list = [self.ui.website_list_widget.item(i).text() for i in range(self.ui.website_list_widget.count())]
            with open(websites_path, 'w') as f: json.dump(website_list, f)
            if platform.system() == "Windows":
                apps_path = self.get_config_path(APP_CONFIG_FILE)
                with open(apps_path, 'w') as f: f.write(self.ui.app_list_edit.toPlainText())
            print(">>> Listas de bloqueio salvas.")
        except Exception as e: print(f"Erro ao salvar listas: {e}")
    def load_lists_from_files(self):
        try:
            websites_path = self.get_config_path(WEBSITE_CONFIG_FILE)
            if os.path.exists(websites_path):
                with open(websites_path, 'r') as f:
                    website_list = json.load(f)
                    self.ui.website_list_widget.clear(); self.ui.website_list_widget.addItems(website_list)
            if platform.system() == "Windows":
                apps_path = self.get_config_path(APP_CONFIG_FILE)
                if os.path.exists(apps_path):
                    with open(apps_path, 'r') as f: self.ui.app_list_edit.setText(f.read())
            print(">>> Listas de bloqueio carregadas.")
        except Exception as e: print(f"Erro ao carregar listas: {e}")
    
    def save_session_history(self, session_duration_seconds):
        app_data_path = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation)
        history_file = os.path.join(app_data_path, "blocker_history.json")
        today_str = datetime.now().strftime("%Y-%m-%d")
        try:
            with open(history_file, 'r') as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            data = {}
        data[today_str] = data.get(today_str, 0) + session_duration_seconds
        os.makedirs(app_data_path, exist_ok=True)
        with open(history_file, 'w') as f:
            json.dump(data, f)
        return data

# Em main.py, substitua toda a sua função update_hosts_file por esta:

    def update_hosts_file(self, blacklist, is_enabled, is_cleanup=False):
        """
        Atualiza o arquivo hosts. Pega cada domínio da blacklist e expande
        para as versões com e sem 'www.' antes de escrever.
        """
        try:
            with open(self.hosts_path, 'r') as f:
                lines = [line for line in f if MARKER not in line]
            
            if is_enabled:
                # Cria um conjunto final para evitar duplicatas e guardar as variações
                final_blacklist = set()
                
                # Para cada domínio limpo da lista, gera as duas variações
                for canonical_domain in blacklist:
                    domain_stripped = canonical_domain.strip()
                    if domain_stripped:
                        final_blacklist.add(domain_stripped)           # Adiciona -> google.com
                        final_blacklist.add('www.' + domain_stripped)  # Adiciona -> www.google.com

                # Escreve a lista final e expandida no arquivo hosts
                for site in sorted(list(final_blacklist)):
                    lines.append(f"{REDIRECT_IP}\t{site}\t{MARKER}\n")
            
            with open(self.hosts_path, 'w') as f:
                f.writelines(lines)
            
            if not is_cleanup and (is_enabled and blacklist):
                self.ui.status_label.setText("Status: Lista de bloqueio atualizada!")
                self.ui.status_label.setStyleSheet("color: green;")
                self.flush_dns()
        except Exception as e:
            self.ui.status_label.setText(f"Hosts Error: {e}. Execute como Admin.")
            self.ui.status_label.setStyleSheet("color: red;")
                  
    def update_exe_blocks(self, blacklist, is_enabled):
        try:
            current_blacklist = {exe.strip().lower() for exe in blacklist if exe.strip()}
            to_unblock = self.previously_blocked_exes - current_blacklist
            for exe in to_unblock: self.unblock_executable(exe)
            if is_enabled:
                to_block = current_blacklist
                for exe in to_block: self.block_executable(exe)
            else:
                to_block = set();
                for exe in self.previously_blocked_exes: self.unblock_executable(exe)
            self.previously_blocked_exes = to_block if is_enabled else set()
            if not self.ui.website_list_widget.count() > 0 and is_enabled: self.ui.status_label.setText("Status: Lista de bloqueio atualizada!"); self.ui.status_label.setStyleSheet("color: #55ff7f;")
        except PermissionError: self.ui.status_label.setText("App Block Error: Acesso negado. Execute como Admin."); self.ui.status_label.setStyleSheet("color: #ff5555;")
        except Exception as e: self.ui.status_label.setText(f"App Block Error: {e}"); self.ui.status_label.setStyleSheet("color: #ff5555;")
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
            self.ui.app_list_edit.setText('\n'.join(sorted(list(blocked_exes))))
            self.previously_blocked_exes = blocked_exes
        except FileNotFoundError: pass
        except Exception as e: print(f"Could not load EXE state: {e}")
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
            self.previously_blocked_exes.discard(exe_name)
        except FileNotFoundError: pass
        except Exception as e: print(f"Error unblocking {exe_name}: {e}")
    def flush_dns(self):
        os_name = platform.system()
        if os_name == "Windows": os.system("ipconfig /flushdns > NUL 2>&1")
        elif os_name == "Linux": print(">>> Flushing Linux DNS cache..."); os.system("sudo systemd-resolve --flush-caches"); print(">>> DNS cache flushed.")
    def get_hosts_path(self):
        if platform.system() == "Windows": return r"C:\Windows\System32\drivers\etc\hosts"
        else: return "/etc/hosts"
    def get_helper_path(self):
        script_dir = os.path.dirname(__file__)
        return os.path.abspath(os.path.join(script_dir, 'blocker_helper.pyw'))
    def toggle_maximize(self):
        """Alterna entre janela maximizada e normal."""
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()
            
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.ui.title_bar.underMouse(): self.old_pos = event.globalPosition().toPoint()
    def mouseMoveEvent(self, event):
        """Move a janela se o mouse estiver sendo arrastado."""
        if self.old_pos:
            delta = QPoint(event.globalPosition().toPoint() - self.old_pos)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event):
        """Finaliza o arraste da janela ao soltar o mouse."""
        self.old_pos = None

    def send_block_time_to_server(self, duration_seconds):
        if not hasattr(self, 'logged_in_user') or not self.logged_in_user:
            print("*** AVISO: Usuário não logado. O tempo não será enviado.")
            return
        server_url = f"{SERVER_BASE_URL}/add_time"
        payload = {'username': self.logged_in_user, 'seconds': duration_seconds}
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
        # Pass the username from the dialog to the main app
        main_app = BlockerApp(login_dialog.successful_username)
        
        # Register cleanup function to be called on exit
        atexit.register(main_app.cleanup_all_blocks)
        
        main_app.show()
        sys.exit(app.exec())
    else:
        # If login is canceled or fails, the program exits
        sys.exit(0)