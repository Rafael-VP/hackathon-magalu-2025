# main.py
import sys
import os
import platform
import json
import atexit
from datetime import datetime
from PyQt6.QtCore import QStandardPaths
from urllib.parse import urlparse
from PyQt6.QtWidgets import QApplication, QWidget, QStyle
from PyQt6.QtCore import Qt, QPoint, QSize, QTimer, QDateTime
from PyQt6.QtGui import QIcon, QPainter, QColor


# Importa o módulo do registro do Windows apenas se estiver no Windows
if platform.system() == "Windows":
    import winreg

# Importa a classe da interface do usuário do arquivo gui.py
from gui import Ui_BlockerApp

# --- FUNÇÕES AUXILIARES E CONSTANTES GLOBAIS ---

def recolor_icon(icon: QIcon, color: QColor) -> QIcon:
    """
    Pega um ícone (QIcon), extrai sua imagem (pixmap) e máscara (forma),
    e retorna um novo ícone com a forma preenchida pela cor desejada.
    Útil para fazer ícones do sistema combinarem com um tema personalizado.
    """
    pixmap = icon.pixmap(QSize(256, 256))
    mask = pixmap.mask()
    pixmap.fill(color)
    pixmap.setMask(mask)
    return QIcon(pixmap)

# Marcador para identificar linhas gerenciadas pelo programa no arquivo hosts
MARKER = "# MANAGED BY PYQT-BLOCKER"
# IP de redirecionamento para bloquear sites
REDIRECT_IP = "127.0.0.1"
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
"""

# --- CLASSE PRINCIPAL DA APLICAÇÃO ---

class BlockerApp(QWidget):
    def __init__(self):
        """Construtor da classe, configura a aplicação na inicialização."""
        super().__init__()
        
        # Configurações iniciais da janela e da interface
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.ui = Ui_BlockerApp()
        self.ui.setupUi(self)
        self._setup_title_bar_icons()
        
        # Propriedades para a lógica da aplicação
        self.old_pos = None
        self.hosts_path = self.get_hosts_path()
        if platform.system() == "Windows":
            self.helper_path = self.get_helper_path()
            self.previously_blocked_exes = set()
        
        # Lista de botões de navegação para fácil gerenciamento
        self.nav_buttons = [
            self.ui.nav_button_timer,
            self.ui.nav_button_lista,
            self.ui.nav_button_rank,
            self.ui.nav_button_estatisticas,
            #self.ui.nav_button_graficos
        ]
        
        # Configuração do timer principal
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_countdown)
        self.total_seconds = 0
        self.end_time = None
        
        # Conecta os sinais e carrega o estado inicial
        self.connect_signals()
        self.load_initial_state()
        self.reset_timer()
        self.change_tab(0)
        self.show()

    # --- MÉTODOS DE LIMPEZA ---

    def cleanup_all_blocks(self):
        """Remove todos os bloqueios aplicados por esta sessão ao fechar."""
        print(">>> Iniciando limpeza de todas as regras de bloqueio...")
        self.update_hosts_file([], False)
        if platform.system() == "Windows":
            for exe in list(self.previously_blocked_exes):
                self.unblock_executable(exe)
        print(">>> Limpeza concluída.")

    def closeEvent(self, event):
        """Intercepta o evento de fechar a janela para executar a limpeza."""
        self.cleanup_all_blocks()
        event.accept()

    # --- MÉTODOS DE CONFIGURAÇÃO DA INTERFACE ---

    def _setup_title_bar_icons(self):
        """Pega os ícones do sistema, os recolore e os aplica aos botões."""
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
        """Conecta os sinais (eventos de clique) dos widgets às suas funções."""
        # Conexões da barra de navegação
        self.ui.nav_button_timer.clicked.connect(lambda: self.change_tab(0))
        self.ui.nav_button_lista.clicked.connect(lambda: self.change_tab(1))
        self.ui.nav_button_rank.clicked.connect(lambda: self.change_tab(2))
        self.ui.nav_button_estatisticas.clicked.connect(lambda: self.change_tab(3))
        #self.ui.nav_button_graficos.clicked.connect(lambda: self.change_tab(4))
        
        # Conexões dos botões da janela
        self.ui.close_button.clicked.connect(self.close)
        self.ui.minimize_button.clicked.connect(self.showMinimized)
        self.ui.maximize_button.clicked.connect(self.toggle_maximize)
        
        # Conexões dos controles de bloqueio
        self.ui.apply_button.clicked.connect(self.apply_all_changes)
        
        # Conexões dos controles do timer
        self.ui.start_button.clicked.connect(self.start_timer)
        self.ui.reset_button.clicked.connect(self.reset_timer)
        
        # Conexões dos controles da lista de URLs
        self.ui.add_url_button.clicked.connect(self.add_url_from_input)
        self.ui.remove_url_button.clicked.connect(self.remove_selected_url)
        self.ui.url_input.returnPressed.connect(self.add_url_from_input)

    # --- MÉTODOS DO GERENCIADOR DE URLS ---
    
    def add_url_from_input(self):
        """Pega o texto do input, valida, limpa e adiciona à lista visual."""
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
                    self.ui.status_label.setText("Status: Domínio já está na lista.")
            else:
                self.ui.status_label.setText("Status: URL inválida.")
        except Exception as e:
            self.ui.status_label.setText(f"Status: Erro ao processar URL - {e}")

    def remove_selected_url(self):
        """Remove o item atualmente selecionado da lista de URLs."""
        list_items = self.ui.website_list_widget.selectedItems()
        if not list_items:
            return
        for item in list_items:
            self.ui.website_list_widget.takeItem(self.ui.website_list_widget.row(item))

    # --- MÉTODOS DO TIMER ---

    def start_timer(self):
        """Inicia o temporizador com o tempo definido nos campos de entrada."""
        hours = int(self.ui.circular_timer.hour_input.text() or 0)
        minutes = int(self.ui.circular_timer.minute_input.text() or 0)
        seconds = int(self.ui.circular_timer.second_input.text() or 0)
        self.total_seconds = (hours * 3600) + (minutes * 60) + seconds
        
        if self.total_seconds > 0:
            self.end_time = QDateTime.currentDateTime().addSecs(self.total_seconds)
            self.timer.start(16)  # Atualiza a cada 16ms para uma animação fluida
            self.ui.start_button.setEnabled(False)
            self.ui.circular_timer.set_inputs_visible(False)

    def update_countdown(self):
        """Chamado pelo QTimer para atualizar o tempo restante e o círculo."""
        now = QDateTime.currentDateTime()
        remaining_msecs = now.msecsTo(self.end_time)
        
        if remaining_msecs <= 0:
            self.timer.stop()
            self.ui.status_label.setText("Status: Timer finalizado!")
            QApplication.beep()
            self.reset_timer()
            return
            
        current_seconds_float = remaining_msecs / 1000.0
        self.ui.circular_timer.set_time(self.total_seconds, current_seconds_float)

    def reset_timer(self):
        """Para e reseta o timer para o valor inicial, mostrando os inputs."""]
        updated_data = self.save_session_history(float(self.total_seconds))
        self.ui.history_graph.load_history(updated_data)
        self.timer.stop()
        h = int(self.ui.circular_timer.hour_input.text() or 0)
        m = int(self.ui.circular_timer.minute_input.text() or 0)
        s = int(self.ui.circular_timer.second_input.text() or 0)
        self.total_seconds = (h * 3600) + (m * 60) + s
        
        self.ui.circular_timer.set_time(self.total_seconds, self.total_seconds)
        self.ui.start_button.setEnabled(True)
        self.ui.circular_timer.set_inputs_visible(True)

    # --- MÉTODOS DE NAVEGAÇÃO E LÓGICA DE BLOQUEIO ---

    def change_tab(self, index):
        """Muda a aba visível e atualiza o estilo dos botões de navegação."""
        self.ui.tabs.setCurrentIndex(index)
        for i, button in enumerate(self.nav_buttons):
            button.setProperty("active", i == index)
            button.style().polish(button)
            
    def apply_all_changes(self):
        """Aplica as mudanças de ambas as listas de bloqueio."""
        is_enabled = self.ui.enable_checkbox.isChecked()
        website_list = [self.ui.website_list_widget.item(i).text() for i in range(self.ui.website_list_widget.count())]
        self.update_hosts_file(website_list, is_enabled)
        
        if platform.system() == "Windows":
             self.update_exe_blocks(self.ui.app_list_edit.toPlainText().split('\n'), is_enabled)

    def load_initial_state(self):
        """Limpa todos os bloqueios anteriores e reseta a interface."""
        self.cleanup_all_blocks()
        self.ui.status_label.setText("Status: Pronto para iniciar.")
        self.ui.website_list_widget.clear()
        if platform.system() == "Windows":
            self.ui.app_list_edit.setText("")
            self.load_exe_block_state()


        app_data_path = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation)
        history_file = os.path.join(app_data_path, "blocker_history.json")
        print(app_data_path)
        try:
            with open(history_file, 'r') as f:
                history_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            history_data = {}
        
        self.ui.history_graph.load_history(history_data)
    
    def save_session_history(self, session_duration_seconds):
        """Reads, updates, and saves the session history to a JSON file."""
        app_data_path = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation)
        history_file = os.path.join(app_data_path, "blocker_history.json")
        
        # Get today's date as a string
        today_str = datetime.now().strftime("%Y-%m-%d")
        
        # Read existing data
        try:
            with open(history_file, 'r') as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            data = {}

        # Update data for today
        data[today_str] = data.get(today_str, 0) + session_duration_seconds
        
        # Write updated data back to the file
        os.makedirs(app_data_path, exist_ok=True)
        with open(history_file, 'w') as f:
            json.dump(data, f)
        
        return data # Return the updated data to refresh the graph

    def update_hosts_file(self, blacklist, is_enabled):
        """Atualiza o arquivo hosts com a lista de URLs a serem bloqueadas."""
        try:
            with open(self.hosts_path, 'r') as f:
                lines = [line for line in f if MARKER not in line]
            
            if is_enabled:
                for site in blacklist:
                    if site.strip():
                        lines.append(f"{REDIRECT_IP}\t{site.strip()}\t{MARKER}\n")
            
            with open(self.hosts_path, 'w') as f:
                f.writelines(lines)
            
            if is_enabled or blacklist:
                self.ui.status_label.setText("Status: Lista de bloqueio atualizada!")
                self.ui.status_label.setStyleSheet("color: green;")
                self.flush_dns()
        except Exception as e:
            self.ui.status_label.setText(f"Hosts Error: {e}. Execute como Admin.")
            self.ui.status_label.setStyleSheet("color: red;")
            
    def update_exe_blocks(self, blacklist, is_enabled):
        """Atualiza o Registro do Windows para bloquear/desbloquear executáveis."""
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
            
            if not self.ui.website_list_widget.count() > 0:
                 self.ui.status_label.setText("Status: Lista de bloqueio atualizada!")
                 self.ui.status_label.setStyleSheet("color: green;")
        except Exception as e:
            self.ui.status_label.setText(f"App Block Error: {e}. Run as Admin.")
            self.ui.status_label.setStyleSheet("color: red;")

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
        """Cria uma chave no Registro para interceptar a execução de um .exe."""
        try:
            key_path = fr"Software\Microsoft\Windows NT\CurrentVersion\Image File Execution Options\{exe_name}"
            with winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, key_path) as key:
                debugger_command = f'"{sys.executable}" "{self.helper_path}"'
                winreg.SetValueEx(key, "Debugger", 0, winreg.REG_SZ, debugger_command)
        except Exception as e:
            print(f"Error blocking {exe_name}: {e}")


    def unblock_executable(self, exe_name):
        """Remove a chave do Registro que bloqueia a execução de um .exe."""
        try:
            key_path = fr"Software\Microsoft\Windows NT\CurrentVersion\Image File Execution Options\{exe_name}"
            winreg.DeleteKey(winreg.HKEY_LOCAL_MACHINE, key_path)
        except Exception as e:
            if not isinstance(e, FileNotFoundError):
                print(f"Error unblocking {exe_name}: {e}")

    # --- MÉTODOS DE SISTEMA E JANELA ---

    def get_hosts_path(self):
        """Retorna o caminho do arquivo hosts dependendo do SO."""
        return r"C:\Windows\System32\drivers\etc\hosts" if platform.system() == "Windows" else "/etc/hosts"

    def get_helper_path(self):
        """Retorna o caminho absoluto para o script auxiliar de bloqueio."""
        return os.path.abspath(os.path.join(os.path.dirname(__file__), 'blocker_helper.pyw'))

    def flush_dns(self):
        """Limpa o cache de DNS do sistema (apenas Windows)."""
        if platform.system() == "Windows":
            os.system("ipconfig /flushdns")

    def toggle_maximize(self):
        """Alterna entre janela maximizada e normal."""
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()
        
    def mousePressEvent(self, event):
        """Captura o clique do mouse na barra de título para iniciar o arraste."""
        if event.button() == Qt.MouseButton.LeftButton and self.ui.title_bar.underMouse():
            self.old_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        """Move a janela se o mouse estiver sendo arrastado."""
        if self.old_pos:
            delta = QPoint(event.globalPosition().toPoint() - self.old_pos)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event):
        """Finaliza o arraste da janela ao soltar o mouse."""
        self.old_pos = None

# --- PONTO DE ENTRADA DA APLICAÇÃO ---

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyleSheet(DARK_THEME)
    ex = BlockerApp()
    # Registra a função de limpeza para ser chamada ao sair
    atexit.register(ex.cleanup_all_blocks)
    sys.exit(app.exec())