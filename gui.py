# gui.py
import os
import sys
import requests
import math
import json
from PyQt6.QtCore import QUrl, Qt, QPoint, QRectF, QSize, QTimer
from PyQt6.QtGui import QColor, QFont, QIcon, QPainter, QPen, QPixmap, QIntValidator
from PyQt6.QtWidgets import (
    QApplication, QCheckBox, QDialog, QFormLayout, QHBoxLayout,
    QLabel, QLineEdit, QStyle, QVBoxLayout, QWidget, QTabWidget,
    QPushButton, QListWidget, QTableWidget, QGraphicsDropShadowEffect
)
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineSettings
from history_graph import HistoryGraph

SERVER_BASE_URL = "http://201.23.72.236:5000"

def recolor_icon(icon: QIcon, color: QColor) -> QIcon:
    pixmap = icon.pixmap(QSize(256, 256))
    mask = pixmap.mask()
    pixmap.fill(color)
    pixmap.setMask(mask)
    return QIcon(pixmap)

def recolor_svg_to_pixmap(svg_path: str, color: QColor, size: QSize) -> QPixmap:
    try:
        with open(svg_path, "r") as f:
            svg_data = f.read()
        
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
        return QPixmap()

class LoginDialog(QDialog):
    # This class is unchanged
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Login")
        self.setModal(True)
        self.setMinimumWidth(400)
        self.successful_username = None
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.old_pos = None
        self.title_bar = QWidget()
        self.title_bar.setObjectName("title_bar")
        self.title_bar.setFixedHeight(35)
        title_bar_layout = QHBoxLayout(self.title_bar)
        title_bar_layout.setContentsMargins(10, 0, 0, 0)
        app_icon_color = QColor("#0078d7")
        colored_pixmap = recolor_svg_to_pixmap("data/icon.svg", app_icon_color, QSize(20, 20))
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(20, 20)
        self.icon_label.setScaledContents(True)
        self.icon_label.setPixmap(colored_pixmap)
        title_label = QLabel('Login to hourGlass')
        title_label.setObjectName("title_label")
        button_icon_color = QColor("white")
        style = QApplication.style()
        self.minimize_button = QPushButton()
        self.minimize_button.setObjectName("minimize_button")
        self.minimize_button.setIcon(recolor_icon(style.standardIcon(QStyle.StandardPixmap.SP_TitleBarMinButton), button_icon_color))
        self.close_button = QPushButton()
        self.close_button.setObjectName("close_button")
        self.close_button.setIcon(recolor_icon(style.standardIcon(QStyle.StandardPixmap.SP_TitleBarCloseButton), button_icon_color))
        title_bar_layout.addWidget(self.icon_label)
        title_bar_layout.addWidget(title_label)
        title_bar_layout.addStretch()
        title_bar_layout.addWidget(self.minimize_button)
        title_bar_layout.addWidget(self.close_button)
        self.minimize_button.setFixedSize(32, 32)
        self.close_button.setFixedSize(32, 32)
        self.minimize_button.setIconSize(QSize(16, 16))
        self.close_button.setIconSize(QSize(16, 16))
        login_title_label = QLabel("Bem-Vindo ao hourClass!")
        login_title_label.setObjectName("login_title")
        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("Digite seu usuário")
        self.password_edit = QLineEdit()
        self.password_edit.setPlaceholderText("Digite sua senha")
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.show_password_checkbox = QCheckBox("Mostrar Senha")
        self.create_user_button = QPushButton("Criar Novo Usuário")
        self.login_button = QPushButton("Entrar")
        self.login_button.setObjectName("primary_button")
        self.cancel_button = QPushButton("Cancelar")
        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: #ff5555;")
        self.error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        form_layout = QFormLayout()
        form_layout.addRow("Usuário:", self.username_edit)
        form_layout.addRow("Senha:", self.password_edit)
        checkbox_layout = QHBoxLayout()
        checkbox_layout.addStretch()
        checkbox_layout.addWidget(self.show_password_checkbox)
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.create_user_button)
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.login_button)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_layout.addWidget(self.title_bar)
        content_layout = QVBoxLayout()
        content_layout.setSpacing(15)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.addWidget(login_title_label)
        content_layout.addLayout(form_layout)
        content_layout.addLayout(checkbox_layout)
        content_layout.addWidget(self.error_label)
        content_layout.addStretch()
        content_layout.addLayout(button_layout)
        main_layout.addLayout(content_layout)
        self.create_user_button.clicked.connect(self.show_register_dialog)
        self.login_button.clicked.connect(self.handle_login)
        self.close_button.clicked.connect(self.reject)
        self.minimize_button.clicked.connect(self.showMinimized)
        self.show_password_checkbox.toggled.connect(self.toggle_password_visibility)
        self.password_edit.returnPressed.connect(self.login_button.click)
    def show_register_dialog(self):
        register_dialog = RegisterDialog(self)
        register_dialog.exec()
    def handle_login(self):
        username = self.username_edit.text()
        password = self.password_edit.text()
        server_url = f"{SERVER_BASE_URL}/login"
        payload = {'username': username, 'password': password}
        try:
            self.login_button.setEnabled(False)
            self.error_label.setText("Conectando...")
            QApplication.processEvents()
            response = requests.post(server_url, json=payload, timeout=10)
            if response.status_code == 200:
                self.successful_username = username
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
    def toggle_password_visibility(self, checked):
        if checked:
            self.password_edit.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.title_bar.underMouse():
            self.old_pos = event.globalPosition().toPoint()
    def mouseMoveEvent(self, event):
        if self.old_pos:
            delta = QPoint(event.globalPosition().toPoint() - self.old_pos)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = event.globalPosition().toPoint()
    def mouseReleaseEvent(self, event):
        self.old_pos = None

class RegisterDialog(QDialog):
    # This class is unchanged
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Criar Novo Usuário")
        self.setModal(True)
        self.setMinimumWidth(350)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.old_pos = None
        self.title_bar = QWidget()
        self.title_bar.setObjectName("title_bar")
        self.title_bar.setFixedHeight(35)
        title_bar_layout = QHBoxLayout(self.title_bar)
        title_bar_layout.setContentsMargins(10, 0, 0, 0)
        app_icon_color = QColor("#0078d7")
        colored_pixmap = recolor_svg_to_pixmap("data/icon.svg", app_icon_color, QSize(20, 20))
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(20, 20)
        self.icon_label.setScaledContents(True)
        self.icon_label.setPixmap(colored_pixmap)
        title_label = QLabel('Register User')
        title_label.setObjectName("title_label")
        button_icon_color = QColor("white")
        style = QApplication.style()
        self.close_button = QPushButton()
        self.close_button.setObjectName("close_button")
        self.close_button.setIcon(recolor_icon(style.standardIcon(QStyle.StandardPixmap.SP_TitleBarCloseButton), button_icon_color))
        title_bar_layout.addWidget(self.icon_label)
        title_bar_layout.addWidget(title_label)
        title_bar_layout.addStretch()
        title_bar_layout.addWidget(self.close_button)
        self.close_button.setFixedSize(32, 32)
        self.close_button.setIconSize(QSize(16, 16))
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
        button_layout.addWidget(self.register_button)
        button_layout.addWidget(self.cancel_button)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_layout.addWidget(self.title_bar)
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.addLayout(form_layout)
        content_layout.addWidget(self.status_label)
        content_layout.addLayout(button_layout)
        main_layout.addLayout(content_layout)
        self.register_button.clicked.connect(self.handle_register)
        self.cancel_button.clicked.connect(self.reject)
        self.close_button.clicked.connect(self.reject)
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
            QApplication.processEvents()
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
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.title_bar.underMouse():
            self.old_pos = event.globalPosition().toPoint()
    def mouseMoveEvent(self, event):
        if self.old_pos:
            delta = QPoint(event.globalPosition().toPoint() - self.old_pos)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = event.globalPosition().toPoint()
    def mouseReleaseEvent(self, event):
        self.old_pos = None

class CircularTimerWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.total_seconds = 0
        self.current_seconds_float = 0.0
        self.page_loaded = False # ADDED: Flag to track if the HTML is ready

        # --- Create and configure the WebEngine view ---
        self.web_view = QWebEngineView(self)
        self.web_view.settings().setAttribute(QWebEngineSettings.WebAttribute.ShowScrollBars, False)
        self.web_view.page().setBackgroundColor(Qt.GlobalColor.transparent)

        # --- Load the local HTML player file ---
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))
        html_path = os.path.join(base_path, "lottie_player.html")
        self.web_view.setUrl(QUrl.fromLocalFile(html_path))

        self.web_view.loadFinished.connect(self._on_load_finished)
        self.web_view.hide()

        # --- Input fields layout ---
        self.hour_input = QLineEdit("00")
        self.hour_input.setObjectName("time_input")
        self.hour_input.setValidator(QIntValidator(0, 99))
        self.hour_input.setMaximumWidth(80) # <<< ADICIONADO: Limita a largura
        self.hour_input.setAlignment(Qt.AlignmentFlag.AlignCenter) # <<< ADICIONADO: Centraliza o texto
        
        self.minute_input = QLineEdit("25")
        self.minute_input.setObjectName("time_input")
        self.minute_input.setValidator(QIntValidator(0, 59))
        self.minute_input.setMaximumWidth(80) # <<< ADICIONADO: Limita a largura
        self.minute_input.setAlignment(Qt.AlignmentFlag.AlignCenter) # <<< ADICIONADO: Centraliza o texto
        
        self.second_input = QLineEdit("00")
        self.second_input.setObjectName("time_input")
        self.second_input.setValidator(QIntValidator(0, 59))
        self.second_input.setMaximumWidth(80) # <<< ADICIONADO: Limita a largura
        self.second_input.setAlignment(Qt.AlignmentFlag.AlignCenter) # <<< ADICIONADO: Centraliza o texto
        
        colon1 = QLabel(":")
        colon1.setObjectName("time_colon")
        colon2 = QLabel(":")
        colon2.setObjectName("time_colon")
        input_layout = QHBoxLayout()
        input_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        input_layout.addStretch()
        input_layout.addWidget(self.hour_input)
        input_layout.addWidget(colon1)
        input_layout.addWidget(self.minute_input)
        input_layout.addWidget(colon2)
        input_layout.addWidget(self.second_input)
        input_layout.addStretch()
        main_layout = QVBoxLayout(self)
        main_layout.addStretch()
        main_layout.addLayout(input_layout)
        main_layout.addStretch()
        self.input_widgets = [self.hour_input, self.minute_input, self.second_input, colon1, colon2]

        # DEPOIS
    # In gui.py, inside the CircularTimerWidget class
    def _on_load_finished(self, success):
        if not success:
            print("Error: Could not load lottie_player.html")
            return
        
        self.page_loaded = True
        
        try:
            json_path_abs = os.path.abspath("data/hourglass.json")
            with open(json_path_abs, 'r', encoding='utf-8') as f:
                animation_data = json.load(f)
                
            json_string_for_js = json.dumps(animation_data)
            
            self.web_view.page().runJavaScript(f"loadAnimation(`{json_string_for_js}`);")

        except Exception as e:
            print(f"Error loading or passing animation data: {e}")

        self.resizeEvent(None)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        
        if not self.page_loaded: return

        rect = self.rect()
        side = min(rect.width(), rect.height())
        
        # ESTA É A LINHA QUE CONTROLA O TAMANHO
        margin = 15
        
        drawing_rect = QRectF((rect.width() - side) / 2 + margin, (rect.height() - side) / 2 + margin, side - 2 * margin, side - 2 * margin)
        
        self.web_view.setGeometry(drawing_rect.toRect())
        self.web_view.page().runJavaScript("resizeAnimation();")

    def set_time(self, total_seconds, current_seconds_float):
        self.total_seconds = total_seconds
        self.current_seconds_float = current_seconds_float

        if not self.page_loaded: return # ADDED: Guard clause
        
        if not self.hour_input.isVisible():
            current_seconds_int = int(math.ceil(self.current_seconds_float))
            hours = current_seconds_int // 3600
            minutes = (current_seconds_int % 3600) // 60
            seconds = current_seconds_int % 60
            
            if self.total_seconds >= 3600:
                time_text = f"{hours:02}:{minutes:02}:{seconds:02}"
                font_size = 30
            else:
                time_text = f"{minutes:02}:{seconds:02}"
                font_size = 40
            
            self.web_view.page().runJavaScript(f"updateText('{time_text}', {font_size});")
        
        self.update()

    def set_inputs_visible(self, visible):
        if not self.page_loaded: return # ADDED: Guard clause
        
        for widget in self.input_widgets:
            widget.setVisible(visible)
        
        if visible:
            self.web_view.hide()
            self.web_view.page().runJavaScript("stopAnimation();")
            self.web_view.page().runJavaScript("updateText('', 0);")
        else:
            self.web_view.show()
            self.web_view.page().runJavaScript("playAnimation();")
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect()
        side = min(rect.width(), rect.height())
        margin = 15
        drawing_rect = QRectF((rect.width() - side) / 2 + margin, (rect.height() - side) / 2 + margin, side - 2 * margin, side - 2 * margin)
        
        painter.setPen(QPen(QColor("#3c3c3c"), 12, Qt.PenStyle.SolidLine))
        painter.drawEllipse(drawing_rect)

        if self.total_seconds > 0 and not self.hour_input.isVisible():
            painter.setPen(QPen(QColor("#0078d7"), 14, Qt.PenStyle.SolidLine))
            progress_ratio = (self.total_seconds - self.current_seconds_float) / self.total_seconds
            arc_angle = progress_ratio * 360
            start_angle = 90 * 16
            span_angle = -int(arc_angle * 16)
            painter.drawArc(drawing_rect, start_angle, span_angle)

# Em gui.py

class Ui_BlockerApp(object):
    def setupUi(self, main_window):
        main_window.setWindowTitle('hourClass')
        primary_screen = QApplication.primaryScreen()
        if primary_screen:
            screen_geometry = primary_screen.availableGeometry()
            width = int(screen_geometry.width() * 0.4)
            height = int(screen_geometry.height() * 0.6)
            main_window.setGeometry(screen_geometry.x(), screen_geometry.y(), width, height)
        
        self.central_widget = QWidget(main_window)
        main_window.setCentralWidget(self.central_widget)

        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(1, 1, 1, 1)
        self.main_layout.setSpacing(0)

        # 1. CRIAR E ADICIONAR A BARRA DE TÍTULO PRIMEIRO
        self.title_bar = QWidget()
        self.title_bar.setObjectName("title_bar")
        self.title_bar.setFixedHeight(35)
        title_bar_layout = QHBoxLayout(self.title_bar)
        title_bar_layout.setContentsMargins(10, 0, 0, 0)
        
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(20, 20)
        self.icon_label.setScaledContents(True)
        
        self.title_label = QLabel('hourClass')
        self.title_label.setObjectName("title_label")
        self.minimize_button = QPushButton()
        self.minimize_button.setObjectName("minimize_button")
        self.maximize_button = QPushButton()
        self.maximize_button.setObjectName("maximize_button")
        self.close_button = QPushButton()
        self.close_button.setObjectName("close_button")
        
        title_bar_layout.addWidget(self.icon_label)
        title_bar_layout.addWidget(self.title_label)
        title_bar_layout.addStretch()
        title_bar_layout.addWidget(self.minimize_button)
        title_bar_layout.addWidget(self.maximize_button)
        title_bar_layout.addWidget(self.close_button)
        self.main_layout.addWidget(self.title_bar)
        
        # 2. DEPOIS, CRIAR E ADICIONAR A BARRA DE NAVEGAÇÃO
        self.nav_bar = QWidget()
        self.nav_bar.setObjectName("nav_bar")
        self.nav_bar.setFixedHeight(50)
        nav_layout = QHBoxLayout(self.nav_bar)
        nav_layout.setContentsMargins(15, 0, 15, 0)
        nav_layout.setSpacing(10)
        
        self.nav_button_timer = QPushButton("Timer")
        self.nav_button_timer.setObjectName("nav_button")
        self.nav_button_lista = QPushButton("Lista")
        self.nav_button_lista.setObjectName("nav_button")
        self.nav_button_estatisticas = QPushButton("Estatísticas")
        self.nav_button_estatisticas.setObjectName("nav_button")
        self.nav_button_rank = QPushButton("Rank")
        self.nav_button_rank.setObjectName("nav_button")
        
        nav_layout.addWidget(self.nav_button_timer)
        nav_layout.addWidget(self.nav_button_lista)
        nav_layout.addWidget(self.nav_button_estatisticas)
        nav_layout.addWidget(self.nav_button_rank)
        nav_layout.addStretch()
        self.main_layout.addWidget(self.nav_bar)

        content_widget = QWidget()
        content_widget.setObjectName("content_widget")
        self.main_layout.addWidget(content_widget)

        # Apply the shadow directly to the content_widget
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)  # Use a larger blur radius for a softer shadow
        shadow.setColor(QColor(0, 0, 0, 180)) # Use a semi-transparent black for a classic shadow effect
        shadow.setOffset(0, 4)
        content_widget.setGraphicsEffect(shadow)
        # Then, create the layout for the content_widget as before
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(15, 15, 15, 15)
        
        self.tabs = QTabWidget()
        self.tabs.tabBar().setVisible(False)
        content_layout.addWidget(self.tabs)

        # ----- Início do conteúdo das abas -----
        timer_page = QWidget()
        timer_page_layout = QVBoxLayout(timer_page)
        self.circular_timer = CircularTimerWidget()
        timer_button_layout = QHBoxLayout()
        line = QWidget(); line.setFixedHeight(1); line.setStyleSheet("background-color: #555;")
        timer_page_layout.addWidget(line)
        sync_layout = QHBoxLayout()
        sync_layout.setContentsMargins(0, 10, 0, 0)
        self.room_input = QLineEdit()
        self.room_input.setPlaceholderText("Nome da Sala")
        self.connect_button = QPushButton("Conectar à Sala")
        self.connect_button.setObjectName("connect_button")
        self.disconnect_button = QPushButton("Desconectar")
        self.sync_status_label = QLabel("Desconectado")
        sync_layout.addWidget(self.room_input)
        sync_layout.addWidget(self.connect_button)
        sync_layout.addWidget(self.disconnect_button)
        sync_layout.addStretch()
        sync_layout.addWidget(self.sync_status_label)
        timer_page_layout.addLayout(sync_layout)
        self.start_button = QPushButton("Start")
        self.start_button.setObjectName("start_button")
        self.reset_button = QPushButton("Reset")
        self.reset_button.setObjectName("reset_button")
        timer_button_layout.addStretch()
        timer_button_layout.addWidget(self.start_button)
        timer_button_layout.addWidget(self.reset_button)
        timer_button_layout.addStretch()
        timer_page_layout.addWidget(self.circular_timer)
        timer_page_layout.addLayout(timer_button_layout)
        self.tabs.addTab(timer_page, "Timer")

        list_page = QWidget()
        list_page_layout = QVBoxLayout(list_page)
        list_page_layout.setContentsMargins(0, 10, 0, 0)
        list_page_layout.setSpacing(10)
        list_page_layout.addWidget(QLabel('Enter domain to block:'))
        add_url_layout = QHBoxLayout()
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Ex: google.com")
        self.add_url_button = QPushButton("Adicionar")
        add_url_layout.addWidget(self.url_input)
        add_url_layout.addWidget(self.add_url_button)
        list_page_layout.addLayout(add_url_layout)
        self.website_list_widget = QListWidget()
        self.remove_url_button = QPushButton("Remover Selecionado")
        list_page_layout.addWidget(self.website_list_widget)
        list_page_layout.addWidget(self.remove_url_button)
        line = QWidget()
        line.setFixedHeight(1)
        line.setStyleSheet("background-color: #555;")
        list_page_layout.addWidget(line)
        list_page_layout.addWidget(QLabel('Enter .exe file to block:'))
        add_app_layout = QHBoxLayout()
        self.app_input = QLineEdit()
        self.app_input.setPlaceholderText("Ex: steam.exe")
        self.add_app_button = QPushButton("Adicionar")
        add_app_layout.addWidget(self.app_input)
        add_app_layout.addWidget(self.add_app_button)
        list_page_layout.addLayout(add_app_layout)
        self.app_list_widget = QListWidget()
        self.remove_app_button = QPushButton("Remover Selecionado")
        list_page_layout.addWidget(self.app_list_widget)
        list_page_layout.addWidget(self.remove_app_button)
        self.enable_checkbox = QCheckBox('Enable Blockers')
        self.apply_button = QPushButton('Apply Blocking Changes')
        self.apply_button.setObjectName("apply_button")
        list_page_layout.addWidget(self.enable_checkbox)
        list_page_layout.addWidget(self.apply_button)
        self.tabs.addTab(list_page, "Lista")

        history_tab = QWidget()
        history_layout = QVBoxLayout(history_tab)
        self.history_graph = HistoryGraph()
        history_layout.addWidget(self.history_graph)
        self.tabs.addTab(history_tab, "Estatísticas")

        rank_tab = QWidget()
        rank_layout = QVBoxLayout(rank_tab)
        rank_layout.setContentsMargins(0, 10, 0, 0)
        self.ranking_table_widget = QTableWidget()
        self.ranking_table_widget.setObjectName("ranking_table_widget")
        rank_layout.addWidget(self.ranking_table_widget)
        self.tabs.addTab(rank_tab, "Rank")
        
        self.status_label = QLabel('Status: Pronto')
        content_layout.addWidget(self.status_label)