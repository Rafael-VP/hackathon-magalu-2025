# main.py
import sys
import os
import requests
import platform
from PyQt6.QtWidgets import QApplication, QWidget, QStyle, QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit, QPushButton, QLabel
from PyQt6.QtCore import Qt, QPoint, QSize, QTimer
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor

if platform.system() == "Windows":
    import winreg

from gui import Ui_BlockerApp

def recolor_icon(icon: QIcon, color: QColor) -> QIcon:
    """Pega um ícone do sistema e retorna uma nova versão na cor desejada usando uma máscara."""
    # Pega o pixmap (a imagem) do ícone em um tamanho padrão
    pixmap = icon.pixmap(QSize(256, 256))
    
    # Extrai a máscara (a forma) do ícone original
    mask = pixmap.mask()
    
    # Preenche a imagem original inteira com a cor desejada
    pixmap.fill(color)
    
    # Aplica a máscara de volta, recortando a forma do ícone na cor sólida
    pixmap.setMask(mask)
    
    return QIcon(pixmap)

# CONSTANTES GLOBAIS
MARKER = "# MANAGED BY PYQT-BLOCKER"
SERVER_BASE_URL = "http://201.23.72.236:5000"
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
    background-color: transparent; border: none;
    padding: 2px;
}
QPushButton#minimize_button:hover, QPushButton#maximize_button:hover { background-color: #555555; }
QPushButton#close_button:hover { background-color: #e81123; }
QTabWidget::pane { border: 1px solid #555; }
QTabBar::tab {
    background: #2b2b2b; padding: 8px 15px;
    border: 1px solid #555; border-bottom: none;
}
QTabBar::tab:selected { background: #3c3c3c; }
"""
#abre a caixa de login
class LoginDialog(QDialog):
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Login")
        self.setModal(True)
        self.username_edit = QLineEdit()
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.create_user_button = QPushButton("Criar Novo Usuário")
        self.login_button = QPushButton("Entrar")
        self.cancel_button = QPushButton("Cancelar")
        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: #ff5555;")
        form_layout = QFormLayout()
        form_layout.addRow("Usuário:", self.username_edit)
        form_layout.addRow("Senha:", self.password_edit)
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.create_user_button)
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.login_button)
        main_layout = QVBoxLayout(self)
        main_layout.addLayout(form_layout)
        main_layout.addWidget(self.error_label)
        main_layout.addLayout(button_layout)
        self.create_user_button.clicked.connect(self.show_register_dialog) 
        self.login_button.clicked.connect(self.handle_login)
        self.cancel_button.clicked.connect(self.reject)

    def show_register_dialog(self):
        register_dialog = RegisterDialog(self)
        register_dialog.exec()

    def handle_login(self):
        username = self.username_edit.text()
        password = self.password_edit.text()
    
        server_url = f"{SERVER_BASE_URL}/login"
    
        payload = {
            'username': username,
            'password': password
        }

        try:
            self.login_button.setEnabled(False)
            self.error_label.setText("Conectando...")
            response = requests.post(server_url, json=payload, timeout=10)
            if response.status_code == 200:
                self.accept()
            elif response.status_code == 401:
                self.error_label.setText("Usuário ou senha inválidos.")
            else:
                self.error_label.setText(f"Erro no servidor: {response.status_code}")
        except requests.exceptions.ConnectionError:
            self.error_label.setText("Erro de conexão com o servidor.")
        except requests.exceptions.Timeout:
            self.error_label.setText("Erro: A conexão demorou para responder.")
        finally:
            self.login_button.setEnabled(True)

class RegisterDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Criar Novo Usuário")
        self.setModal(True)
        self.setMinimumWidth(350)
        self.username_edit = QLineEdit()
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_password_edit = QLineEdit()
        self.confirm_password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.register_button = QPushButton("Registrar")
        self.cancel_button = QPushButton("Cancelar")
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #ff5555;")
        form_layout = QFormLayout()
        form_layout.addRow("Usuário:", self.username_edit)
        form_layout.addRow("Senha:", self.password_edit)
        form_layout.addRow("Confirmar Senha:", self.confirm_password_edit)
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.register_button)
        main_layout = QVBoxLayout(self)
        main_layout.addLayout(form_layout)
        main_layout.addWidget(self.status_label)
        main_layout.addLayout(button_layout)
        self.register_button.clicked.connect(self.handle_register)
        self.cancel_button.clicked.connect(self.reject)

    def handle_register(self):
        username = self.username_edit.text()
        password = self.password_edit.text()
        confirm_password = self.confirm_password_edit.text()

        if not username or not password:
            self.status_label.setText("Usuário e senha não podem estar vazios.")
            return
        if password != confirm_password:
            self.status_label.setText("As senhas não coincidem.")
            return

        server_url = f"{SERVER_BASE_URL}/register"
        payload = {'username': username, 'password': password}

        try:
            self.register_button.setEnabled(False)
            self.status_label.setText("Registrando...")
            response = requests.post(server_url, json=payload, timeout=10)
            if response.status_code == 201:
                self.status_label.setStyleSheet("color: #55ff7f;")
                self.status_label.setText("Usuário criado! Você já pode fazer o login.")
                QTimer.singleShot(2000, self.accept)
            elif response.status_code == 409:
                self.status_label.setStyleSheet("color: #ff5555;")
                self.status_label.setText("Este nome de usuário já existe.")
            else:
                self.status_label.setStyleSheet("color: #ff5555;")
                self.status_label.setText(f"Erro no servidor: {response.status_code}")
        except requests.exceptions.RequestException:
            self.status_label.setStyleSheet("color: #ff5555;")
            self.status_label.setText("Erro de conexão com o servidor.")
        finally:
            self.register_button.setEnabled(True)
            
class BlockerApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.ui = Ui_BlockerApp()
        self.ui.setupUi(self)
        
        self._setup_title_bar_icons()
        
        self.old_pos = None
        self.hosts_path = self.get_hosts_path()
        self.helper_path = self.get_helper_path()
        self.previously_blocked_exes = set()
        
        self.connect_signals()
        self.load_initial_state()
        self.show()

    def _setup_title_bar_icons(self):
        """Pega os ícones do sistema, os recolore para branco e os aplica."""
        style = self.style()
        
        minimize_icon = style.standardIcon(QStyle.StandardPixmap.SP_TitleBarMinButton)
        maximize_icon = style.standardIcon(QStyle.StandardPixmap.SP_TitleBarMaxButton)
        close_icon = style.standardIcon(QStyle.StandardPixmap.SP_TitleBarCloseButton)

        icon_color = QColor("white")

        white_minimize_icon = recolor_icon(minimize_icon, icon_color)
        white_maximize_icon = recolor_icon(maximize_icon, icon_color)
        white_close_icon = recolor_icon(close_icon, icon_color)
        
        self.ui.minimize_button.setIcon(white_minimize_icon)
        self.ui.maximize_button.setIcon(white_maximize_icon)
        self.ui.close_button.setIcon(white_close_icon)
        
        self.ui.minimize_button.setFixedSize(32, 32)
        self.ui.maximize_button.setFixedSize(32, 32)
        self.ui.close_button.setFixedSize(32, 32)
        self.ui.minimize_button.setIconSize(QSize(16, 16))
        self.ui.maximize_button.setIconSize(QSize(16, 16))
        self.ui.close_button.setIconSize(QSize(16, 16))

    # --- O resto do arquivo permanece o mesmo de antes ---
    def connect_signals(self):
        self.apply_button.clicked.connect(self.apply_all_changes)
        self.ui.close_button.clicked.connect(self.close)
        self.ui.minimize_button.clicked.connect(self.showMinimized)
        self.ui.maximize_button.clicked.connect(self.toggle_maximize)

    def apply_all_changes(self):
        is_enabled = self.enable_checkbox.isChecked()
        self.update_hosts_file(self.website_list_edit.toPlainText().split('\n'), is_enabled)
        if platform.system() == "Windows":
            self.update_exe_blocks(self.app_list_edit.toPlainText().split('\n'), is_enabled)

    def load_initial_state(self):
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
        except Exception:
            self.status_label.setText(f"Status: Error loading hosts file.")
        if platform.system() == "Windows": self.load_exe_block_state()

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

    # 1. Cria e executa a janela de login primeiro
    login_dialog = LoginDialog()
    
    # login_dialog.exec() pausa o código aqui até que o diálogo seja fechado
    # e retorna se foi aceito (login OK) ou rejeitado (cancelado).
    if login_dialog.exec() == QDialog.DialogCode.Accepted:
        # 2. Se o login foi bem-sucedido, cria e mostra a janela principal
        main_app = BlockerApp()
        main_app.show() # A chamada .show() agora está aqui
        sys.exit(app.exec())
    else:
        # 3. Se o login foi cancelado ou falhou, o programa simplesmente termina
        sys.exit(0)