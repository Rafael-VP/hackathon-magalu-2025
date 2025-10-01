# gui.py
import requests
import math
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit,
    QPushButton, QCheckBox, QApplication, QTabWidget,
    QLineEdit, QListWidget, QDialog, QFormLayout, QStyle
)
from PyQt6.QtGui import QScreen, QPainter, QColor, QPen, QFont, QIntValidator, QPixmap, QIcon
from PyQt6.QtCore import Qt, QRectF, QTimer, QSize, QPoint
from PyQt6.QtSvg import QSvgRenderer
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
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Login")
        self.setModal(True)
        self.setMinimumWidth(400)
        self.successful_username = None

        # --- MAKE WINDOW FRAMELESS ---
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.old_pos = None
        
        # --- CUSTOM TITLE BAR ---
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
        
        # --- LOGIN FORM WIDGETS ---
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

        # --- LAYOUT SETUP ---
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

        # --- SIGNAL CONNECTIONS ---
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
        """Toggles the visibility of the password field."""
        if checked:
            self.password_edit.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)

    # --- DRAGGING FUNCTIONS ---
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
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Criar Novo Usuário")
        self.setModal(True)
        self.setMinimumWidth(350)

        # --- MAKE WINDOW FRAMELESS ---
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.old_pos = None

        # --- CUSTOM TITLE BAR ---
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

        # --- REGISTER FORM WIDGETS ---
        self.username_edit = QLineEdit()
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_password_edit = QLineEdit()
        self.confirm_password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.register_button = QPushButton("Registrar")
        self.cancel_button = QPushButton("Cancelar")
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #ff5555;")
        
        # --- LAYOUT SETUP ---
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

        # --- SIGNAL CONNECTIONS ---
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

    # --- DRAGGING FUNCTIONS ---
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
        self.rotation_angle = 0

        self.start_color = QColor("#3C3C3C")
        self.end_color = QColor("#0078d7")
        try:
            self.base_hourglass_icon = QIcon("data/hourglass.svg")
        except Exception as e:
            print(f"Could not load hourglass.svg: {e}")
            self.base_hourglass_icon = None
        
        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self._update_rotation)
        self.animation_timer.start(50)

        self.hour_input = QLineEdit("00")
        self.hour_input.setObjectName("time_input")
        self.hour_input.setValidator(QIntValidator(0, 99))
        self.minute_input = QLineEdit("25")
        self.minute_input.setObjectName("time_input")
        self.minute_input.setValidator(QIntValidator(0, 59))
        self.second_input = QLineEdit("00")
        self.second_input.setObjectName("time_input")
        self.second_input.setValidator(QIntValidator(0, 59))
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

    def _update_rotation(self):
        if not self.hour_input.isVisible():
            self.rotation_angle = (self.rotation_angle + 3) % 360
            self.update()

    def set_time(self, total_seconds, current_seconds_float):
        self.total_seconds = total_seconds
        self.current_seconds_float = current_seconds_float
        self.update()

    def set_inputs_visible(self, visible):
        for widget in self.input_widgets:
            widget.setVisible(visible)
        if visible:
            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect()
        side = min(rect.width(), rect.height())
        margin = 15
        drawing_rect = QRectF((rect.width() - side) / 2 + margin, (rect.height() - side) / 2 + margin, side - 2 * margin, side - 2 * margin)
        
        bg_pen = QPen(QColor("#3c3c3c"), 12, Qt.PenStyle.SolidLine)
        painter.setPen(bg_pen)
        painter.drawEllipse(drawing_rect)

        progress_ratio = 0
        if self.total_seconds > 0:
            progress_pen = QPen(QColor("#0078d7"), 14, Qt.PenStyle.SolidLine)
            painter.setPen(progress_pen)
            elapsed_seconds = self.total_seconds - self.current_seconds_float
            progress_ratio = elapsed_seconds / self.total_seconds
            arc_angle = progress_ratio * 360
            start_angle = 90 * 16
            span_angle = -int(arc_angle * 16)
            painter.drawArc(drawing_rect, start_angle, span_angle)

        if self.base_hourglass_icon:
            r1, g1, b1, _ = self.start_color.getRgb()
            r2, g2, b2, _ = self.end_color.getRgb()
            r = r1 + (r2 - r1) * progress_ratio
            g = g1 + (g2 - g1) * progress_ratio
            b = b1 + (b2 - b1) * progress_ratio
            current_color = QColor(int(r), int(g), int(b))
            
            current_colored_icon = recolor_icon(self.base_hourglass_icon, current_color)
            current_pixmap = current_colored_icon.pixmap(QSize(256, 256))

            painter.save()
            angle_to_use = self.rotation_angle if not self.hour_input.isVisible() else 0
            icon_size = drawing_rect.width() * 0.8
            icon_rect = QRectF(-icon_size / 2, -icon_size / 2, icon_size, icon_size)
            painter.translate(drawing_rect.center())
            painter.rotate(angle_to_use)
            painter.drawPixmap(icon_rect.toRect(), current_pixmap)
            painter.restore()
        
        if not self.hour_input.isVisible():
            current_seconds_int = int(self.current_seconds_float) + 1 if self.current_seconds_float > 0 else 0
            hours = current_seconds_int // 3600
            minutes = (current_seconds_int % 3600) // 60
            seconds = current_seconds_int % 60
            if self.total_seconds >= 3600:
                time_text = f"{hours:02}:{minutes:02}:{seconds:02}"
                font_size = 30
            else:
                time_text = f"{minutes:02}:{seconds:02}"
                font_size = 40
            font = QFont("Segoe UI", font_size)
            font.setBold(True)
            painter.setFont(font)
            painter.setPen(QColor("#f0f0f0"))
            painter.drawText(drawing_rect, Qt.AlignmentFlag.AlignCenter, time_text)

class Ui_BlockerApp(object):
    def setupUi(self, main_window):
        main_window.setWindowTitle('hourClass')
        screen = QScreen.availableGeometry(QApplication.primaryScreen())
        width = int(screen.width() * 0.4)
        height = int(screen.height() * 0.6)
        main_window.setGeometry(screen.x(), screen.y(), width, height)
        self.main_layout = QVBoxLayout(main_window)
        self.main_layout.setContentsMargins(1, 1, 1, 1)
        self.main_layout.setSpacing(0)
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
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(15, 0, 15, 15)
        self.main_layout.addWidget(content_widget)
        
        self.tabs = QTabWidget()
        self.tabs.tabBar().setVisible(False)
        
        timer_page = QWidget()
        timer_page_layout = QVBoxLayout(timer_page)
        self.circular_timer = CircularTimerWidget()
        timer_button_layout = QHBoxLayout()
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
        list_page_layout.addWidget(QLabel('Enter URL to block:'))
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
        list_page_layout.addWidget(QLabel('Enter .exe files to block:'))
        self.app_list_edit = QTextEdit()
        list_page_layout.addWidget(self.app_list_edit)
        self.enable_checkbox = QCheckBox('Enable Blockers')
        self.apply_button = QPushButton('Apply Blocking Changes')
        list_page_layout.addWidget(self.enable_checkbox)
        list_page_layout.addWidget(self.apply_button)
        self.tabs.addTab(list_page, "Lista")

        history_tab = QWidget()
        history_layout = QVBoxLayout(history_tab)
        self.history_graph = HistoryGraph()
        history_layout.addWidget(self.history_graph)
        self.tabs.addTab(history_tab, "Estatísticas")

        rank_tab = QWidget()
        rank_tab.setLayout(QVBoxLayout())
        rank_tab.layout().addWidget(QLabel("Página de Rank"))
        self.tabs.addTab(rank_tab, "Rank")
        
        content_layout.addWidget(self.tabs)
        self.status_label = QLabel('Status: Ready')
        content_layout.addWidget(self.status_label)