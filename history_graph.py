# history_graph.py
from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QColor, QFont
from PyQt6.QtCore import QRect, QDate, Qt
from datetime import datetime, timedelta

SQUARE_SIZE = 15
SQUARE_SPACING = 4
# Define the height of the graph grid
GRAPH_HEIGHT = 7 * (SQUARE_SIZE + SQUARE_SPACING)
TEXT_AREA_HEIGHT = 40 # Reserve space for the text below the graph

class HistoryGraph(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.history_data = {}
        self.setMouseTracking(True)

    def load_history(self, data):
        """Loads history data and triggers a repaint."""
        self.history_data = data
        self.update()

    def paintEvent(self, event):
        """Draws the centered history graph and text."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        today = datetime.now()
        max_value = max(self.history_data.values()) if self.history_data else 1

        # Calculate the vertical offset for centering ---
        total_content_height = GRAPH_HEIGHT + TEXT_AREA_HEIGHT
        y_offset = (self.height() - total_content_height) / 2
        # Ensure the offset isn't negative if the widget is too small
        if y_offset < 0:
            y_offset = 0

        # Draw the squares with the offset
        for i in range(366):
            date = today - timedelta(days=i)
            date_str = date.strftime("%Y-%m-%d")
            
            week_ago = (today.date() - date.date()).days // 7
            day_of_week = date.weekday() # Monday is 0, Sunday is 6
            
            x = self.width() - (week_ago + 1) * (SQUARE_SIZE + SQUARE_SPACING)
            # Apply the offset when calculating the square's y-position
            y = y_offset + (day_of_week * (SQUARE_SIZE + SQUARE_SPACING))

            value = self.history_data.get(date_str, 0)
            if value == 0:
                color = QColor("#3c3c3c")
            else:
                # Calculate progress from 0.0 to 1.0
                progress = value / max_value

                # Interpolate Green from 50 up to 120 (the green value in #0078d7)
                green_val = 50 + int(progress * 70)

                # Interpolate Blue from a darker base up to 215 (the blue value in #0078d7)
                blue_val = 100 + int(progress * 115)

                color = QColor(0, green_val, blue_val)
            
            painter.setBrush(color)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRect(int(x), int(y), SQUARE_SIZE, SQUARE_SIZE)
            
        # Draw the text information with the offset
        today_str = today.strftime("%Y-%m-%d")
        today_seconds = self.history_data.get(today_str, 0)
        today_minutes = today_seconds // 60
        display_text = f"Today ({today.strftime('%B %d')}): {today_minutes} minutes of focus"

        # 3. Apply the offset when defining the text area
        text_y_position = y_offset + GRAPH_HEIGHT + 10
        text_rect = QRect(0, int(text_y_position), self.width(), 30)

        font = QFont("Segoe UI", 14)
        painter.setFont(font)
        painter.setPen(QColor("#a9a9a9"))
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, display_text)

    def mouseMoveEvent(self, event):
        """Handle tooltips, adjusting for the vertical offset."""
        today = datetime.now()
        x, y = event.pos().x(), event.pos().y()
        total_content_height = GRAPH_HEIGHT + TEXT_AREA_HEIGHT
        y_offset = (self.height() - total_content_height) / 2
        if y_offset < 0: y_offset = 0
        
        # Adjust y-coordinate for hit testing
        adjusted_y = y - y_offset
        
        week_ago = (self.width() - x) // (SQUARE_SIZE + SQUARE_SPACING)
        day_of_week = int(adjusted_y // (SQUARE_SIZE + SQUARE_SPACING))
        
        if 0 <= day_of_week <= 6:
            date = today - timedelta(days=(week_ago * 7 + (today.weekday() - day_of_week)))
            date_str = date.strftime("%Y-%m-%d")
            
            value_seconds = self.history_data.get(date_str, 0)
            minutes = value_seconds // 60
            
            self.setToolTip(f"{minutes} minutes on {date.strftime('%B %d, %Y')}")
        else:
            self.setToolTip("")