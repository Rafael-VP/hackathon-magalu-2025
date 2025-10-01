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
        # Cache for hit-testing to avoid recalculating on every mouse move
        self.squares_rects = {}

    def load_history(self, data):
        """Loads history data and triggers a repaint."""
        self.history_data = data
        self.update()

    def paintEvent(self, event):
        """Draws the centered history graph and text."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.squares_rects.clear() # Clear cache before redrawing

        today = datetime.now()
        # Use 'or [1]' to prevent error on max() with an empty sequence
        max_value = max(self.history_data.values() or [1])
        
        # Calculate the total number of columns
        num_columns = 53 # A year fits into 52 weeks and a few days

        # Calculate the total width and height of the grid
        total_graph_width = num_columns * (SQUARE_SIZE + SQUARE_SPACING)
        total_content_height = GRAPH_HEIGHT + TEXT_AREA_HEIGHT

        # Calculate horizontal and vertical offsets for centering
        x_offset = (self.width() - total_graph_width) / 2
        y_offset = (self.height() - total_content_height) / 2
        
        # Ensure offsets aren't negative if the window is smaller than the graph
        x_offset = max(0, x_offset)
        y_offset = max(0, y_offset)

        # Draw the squares for the last 366 days
        for i in range(365, -1, -1): # Iterate backwards to draw from left to right
            date = today - timedelta(days=i)
            date_str = date.strftime("%Y-%m-%d")
            
            # This is day number from the start of the year (1-366)
            day_of_year = date.timetuple().tm_yday
            # Correctly calculate the week number and day of week
            week_index = (date.weekday() + (today - date).days) // 7
            day_of_week = date.weekday() # Monday is 0

            # Today's column is the last one
            column = num_columns - 1 - week_index
            
            x = x_offset + column * (SQUARE_SIZE + SQUARE_SPACING)
            y = y_offset + day_of_week * (SQUARE_SIZE + SQUARE_SPACING)

            value = self.history_data.get(date_str, 0)
            if value == 0:
                color = QColor("#3c3c3c")
            else:
                progress = min(value / max_value, 1.0) # Cap progress at 1.0
                # Interpolate color from a light blue to a dark blue
                r = 40
                g = int(80 + (100 * progress))
                b = int(150 + (105 * progress))
                color = QColor(r, g, b)
            
            painter.setBrush(color)
            painter.setPen(Qt.PenStyle.NoPen)
            rect = QRect(int(x), int(y), SQUARE_SIZE, SQUARE_SIZE)
            painter.drawRect(rect)
            # Store the rect and its corresponding date string for tooltips
            self.squares_rects[rect] = date_str
            
        # Draw the text information with the vertical offset
        today_str = today.strftime("%Y-%m-%d")
        today_seconds = self.history_data.get(today_str, 0)
        today_minutes = today_seconds // 60
        display_text = f"Today ({today.strftime('%B %d')}): {today_minutes} minutes of focus"

        text_y_position = y_offset + GRAPH_HEIGHT + 10
        text_rect = QRect(0, int(text_y_position), self.width(), 30)

        font = QFont("Segoe UI", 14)
        painter.setFont(font)
        painter.setPen(QColor("#a9a9a9"))
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, display_text)

    def mouseMoveEvent(self, event):
        """Handle tooltips by checking if the mouse is inside any cached rect."""
        pos = event.pos()
        # Find which square the mouse is over
        for rect, date_str in self.squares_rects.items():
            if rect.contains(pos):
                value_seconds = self.history_data.get(date_str, 0)
                minutes = value_seconds // 60
                date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                self.setToolTip(f"{minutes} minutes on {date_obj.strftime('%B %d, %Y')}")
                return # Exit after finding the first match
        
        # If no square is found, clear the tooltip
        self.setToolTip("")