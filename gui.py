# gui.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit,
    QPushButton, QCheckBox, QApplication, QTabWidget, QStyle
)
from PyQt6.QtGui import QScreen
from PyQt6.QtCore import Qt

class Ui_BlockerApp(object):
    def setupUi(self, main_window):
        # --- Configuração Básica da Janela ---
        main_window.setWindowTitle('PyQt System Blocker')
        screen = QScreen.availableGeometry(QApplication.primaryScreen())
        width = int(screen.width() * 0.4)
        height = int(screen.height() * 0.5)
        main_window.setGeometry(screen.x(), screen.y(), width, height)

        # --- Layout Principal ---
        self.main_layout = QVBoxLayout(main_window)
        self.main_layout.setContentsMargins(1, 1, 1, 1)
        self.main_layout.setSpacing(0)

        # --- Barra de Título Personalizada ---
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

        # --- INÍCIO DA MODIFICAÇÃO: 5 BOTÕES DE NAVEGAÇÃO ---
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
        # --- FIM DA MODIFICAÇÃO ---
        
        # --- Área de Conteúdo ---
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(15, 0, 15, 15)
        self.main_layout.addWidget(content_widget)

        # --- Widget de Abas (com 5 páginas) ---
        self.tabs = QTabWidget()
        self.tabs.tabBar().setVisible(False)
        
        # Página 1: Timer (antigo Website Blocker)
        website_tab = QWidget()
        website_layout = QVBoxLayout(website_tab)
        website_layout.setContentsMargins(0, 10, 0, 0)
        self.website_list_edit = QTextEdit()
        website_layout.addWidget(QLabel('Enter websites to block (one per line):'))
        website_layout.addWidget(self.website_list_edit)
        self.tabs.addTab(website_tab, "Timer")

        # Página 2: Lista (antigo Application Blocker)
        app_tab = QWidget()
        app_layout = QVBoxLayout(app_tab)
        app_layout.setContentsMargins(0, 10, 0, 0)
        self.app_list_edit = QTextEdit()
        app_layout.addWidget(QLabel('Enter .exe files to block (e.g., Spotify.exe):'))
        app_layout.addWidget(self.app_list_edit)
        self.tabs.addTab(app_tab, "Lista")
        
        # Páginas 3, 4, 5 (Novas e em branco)
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
        
        # --- Controles Globais ---
        self.enable_checkbox = QCheckBox('Enable All Blockers')
        self.enable_checkbox.setChecked(True)
        content_layout.addWidget(self.enable_checkbox)
        
        self.apply_button = QPushButton('Apply Changes')
        content_layout.addWidget(self.apply_button)
        
        self.status_label = QLabel('Status: Ready')
        content_layout.addWidget(self.status_label)

        # --- Anexa widgets para a lógica ---
        main_window.tabs = self.tabs
        main_window.nav_button_timer = self.nav_button_timer
        main_window.nav_button_lista = self.nav_button_lista
        main_window.nav_button_rank = self.nav_button_rank
        main_window.nav_button_estatisticas = self.nav_button_estatisticas
        main_window.nav_button_graficos = self.nav_button_graficos
        main_window.website_list_edit = self.website_list_edit
        main_window.app_list_edit = self.app_list_edit
        main_window.enable_checkbox = self.enable_checkbox
        main_window.apply_button = self.apply_button
        main_window.status_label = self.status_label