# gui.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit,
    QPushButton, QCheckBox, QApplication, QTabWidget, QStyle,
    QLineEdit, QListWidget
)
from PyQt6.QtGui import QScreen, QPainter, QColor, QPen, QFont, QIntValidator
from PyQt6.QtCore import Qt, QRectF

class CircularTimerWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.total_seconds = 0
        self.current_seconds_float = 0.0

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

    def set_time(self, total_seconds, current_seconds_float):
        self.total_seconds = total_seconds
        self.current_seconds_float = current_seconds_float
        self.update()

    def set_inputs_visible(self, visible):
        for widget in self.input_widgets:
            widget.setVisible(visible)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect()
        side = min(rect.width(), rect.height())
        margin = 15
        
        drawing_rect = QRectF(
            (rect.width() - side) / 2 + margin,
            (rect.height() - side) / 2 + margin,
            side - 2 * margin,
            side - 2 * margin
        )

        bg_pen = QPen(QColor("#3c3c3c"), 12, Qt.PenStyle.SolidLine)
        painter.setPen(bg_pen)
        painter.drawEllipse(drawing_rect)

        if self.total_seconds > 0:
            progress_pen = QPen(QColor("#0078d7"), 14, Qt.PenStyle.SolidLine)
            painter.setPen(progress_pen)
            
            elapsed_seconds = self.total_seconds - self.current_seconds_float
            progress_ratio = elapsed_seconds / self.total_seconds if self.total_seconds > 0 else 0
            arc_angle = progress_ratio * 360
            start_angle = 90 * 16
            span_angle = -int(arc_angle * 16)
            
            painter.drawArc(drawing_rect, start_angle, span_angle)

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
        main_window.setWindowTitle('PyQt System Blocker')
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
        
        self.title_label = QLabel('PyQt System Blocker')
        self.title_label.setObjectName("title_label")
        
        self.minimize_button = QPushButton()
        self.minimize_button.setObjectName("minimize_button")
        
        self.maximize_button = QPushButton()
        self.maximize_button.setObjectName("maximize_button")
        
        self.close_button = QPushButton()
        self.close_button.setObjectName("close_button")
        
        title_bar_layout.addWidget(self.title_label)
        title_bar_layout.addStretch()
        title_bar_layout.addWidget(self.minimize_button)
        title_bar_layout.addWidget(self.maximize_button)
        title_bar_layout.addWidget(self.close_button)
        self.main_layout.addWidget(self.title_bar)
        
        # --- Barra de Navegação ---
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
        self.nav_button_rank = QPushButton("Rank")
        self.nav_button_rank.setObjectName("nav_button")
        self.nav_button_estatisticas = QPushButton("Estatísticas")
        self.nav_button_estatisticas.setObjectName("nav_button")
        self.nav_button_graficos = QPushButton("Gráficos")
        self.nav_button_graficos.setObjectName("nav_button")
        
        nav_layout.addWidget(self.nav_button_timer)
        nav_layout.addWidget(self.nav_button_lista)
        nav_layout.addWidget(self.nav_button_rank)
        nav_layout.addWidget(self.nav_button_estatisticas)
        nav_layout.addWidget(self.nav_button_graficos)
        nav_layout.addStretch()
        self.main_layout.addWidget(self.nav_bar)
        
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(15, 0, 15, 15)
        self.main_layout.addWidget(content_widget)
        
        self.tabs = QTabWidget()
        self.tabs.tabBar().setVisible(False)
        
        # Página 1: Timer
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

        # Página 2: Lista
        list_page = QWidget()
        list_page_layout = QVBoxLayout(list_page)
        list_page_layout.setContentsMargins(0, 10, 0, 0)
        list_page_layout.setSpacing(10)
        
        # --- MODIFICAÇÃO: Início do novo sistema de gerenciamento de URLs ---
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

        # Divisor visual para separar as duas listas
        line = QWidget()
        line.setFixedHeight(1)
        line.setStyleSheet("background-color: #555;")
        list_page_layout.addWidget(line)
        # --- FIM da modificação do sistema de URLs ---

        # Lista de Aplicativos (inalterada)
        list_page_layout.addWidget(QLabel('Enter .exe files to block:'))
        self.app_list_edit = QTextEdit()
        list_page_layout.addWidget(self.app_list_edit)
        
        # Controles de bloqueio (Enable/Apply)
        self.enable_checkbox = QCheckBox('Enable Blockers')
        self.apply_button = QPushButton('Apply Blocking Changes')
        list_page_layout.addWidget(self.enable_checkbox)
        list_page_layout.addWidget(self.apply_button)
        self.tabs.addTab(list_page, "Lista")
        
        # Outras Páginas
        rank_tab = QWidget()
        rank_tab.setLayout(QVBoxLayout())
        rank_tab.layout().addWidget(QLabel("Página de Rank"))
        self.tabs.addTab(rank_tab, "Rank")
        
        stats_tab = QWidget()
        stats_tab.setLayout(QVBoxLayout())
        stats_tab.layout().addWidget(QLabel("Página de Estatísticas"))
        self.tabs.addTab(stats_tab, "Estatísticas")
        
        charts_tab = QWidget()
        charts_tab.setLayout(QVBoxLayout())
        charts_tab.layout().addWidget(QLabel("Página de Gráficos"))
        self.tabs.addTab(charts_tab, "Gráficos")
        
        content_layout.addWidget(self.tabs)
        self.status_label = QLabel('Status: Ready')
        content_layout.addWidget(self.status_label)
        
        # Bloco essencial para anexar widgets à janela principal
        main_window.tabs = self.tabs
        main_window.nav_button_timer = self.nav_button_timer
        main_window.nav_button_lista = self.nav_button_lista
        main_window.nav_button_rank = self.nav_button_rank
        main_window.nav_button_estatisticas = self.nav_button_estatisticas
        main_window.nav_button_graficos = self.nav_button_graficos
        main_window.circular_timer = self.circular_timer
        main_window.start_button = self.start_button
        main_window.reset_button = self.reset_button
        
        # Anexa os novos widgets da lista de URLs
        main_window.url_input = self.url_input
        main_window.add_url_button = self.add_url_button
        main_window.website_list_widget = self.website_list_widget
        main_window.remove_url_button = self.remove_url_button
        
        main_window.app_list_edit = self.app_list_edit
        main_window.enable_checkbox = self.enable_checkbox
        main_window.apply_button = self.apply_button
        main_window.status_label = self.status_label