# history_graph.py
from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QColor
from PyQt6.QtCore import Qt
from datetime import datetime, timedelta

SQUARE_SIZE = 15
SQUARE_SPACING = 4

class HistoryGraph(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.history_data = {}
        self.setMouseTracking(True) # Enable mouse move events for tooltips

    def load_history(self, data):
        """Loads history data and triggers a repaint."""
        self.history_data = data
        self.update() # Schedule a repaint

    def paintEvent(self, event):
        """Draws the history graph."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        today = datetime.now()
        
        # Find max value for color scaling
        max_value = max(self.history_data.values()) if self.history_data else 1

        # Iterate back through the last year (approx 53 weeks)
        for i in range(366):
            date = today - timedelta(days=i)
            date_str = date.strftime("%Y-%m-%d")

            # Calculate position in the grid
            week_ago = (today.date() - date.date()).days // 7
            day_of_week = date.weekday() # Monday is 0, Sunday is 6
            
            x = self.width() - (week_ago + 1) * (SQUARE_SIZE + SQUARE_SPACING)
            y = day_of_week * (SQUARE_SIZE + SQUARE_SPACING)

            # Determine color based on activity
            value = self.history_data.get(date_str, 0)
            if value == 0:
                color = QColor("#3c3c3c") # No activity
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
            painter.drawRect(x, y, SQUARE_SIZE, SQUARE_SIZE)
    
    def mouseMoveEvent(self, event):
        """Show tooltips with date and activity information."""
        today = datetime.now()
        
        # Reverse calculate which square the mouse is over
        x, y = event.pos().x(), event.pos().y()
        
        week_ago = (self.width() - x) // (SQUARE_SIZE + SQUARE_SPACING)
        day_of_week = y // (SQUARE_SIZE + SQUARE_SPACING)
        
        if 0 <= day_of_week <= 6:
            date = today - timedelta(days=(week_ago * 7 + (today.weekday() - day_of_week)))
            date_str = date.strftime("%Y-%m-%d")
            
            value_seconds = self.history_data.get(date_str, 0)
            minutes = value_seconds // 60
            
            self.setToolTip(f"{minutes} minutes on {date.strftime('%B %d, %Y')}")
        else:
            self.setToolTip("")