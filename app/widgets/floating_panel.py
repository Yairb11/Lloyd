from PyQt6.QtCore import QEvent, QObject, QPoint, QRect, Qt, pyqtSignal
from PyQt6.QtGui import QCursor
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from app.config import (
    COLOR_CLOSE_BUTTON_BG, COLOR_CLOSE_BUTTON_HOVER_BG, COLOR_CLOSE_BUTTON_TEXT,
    COLOR_PANEL_ACTION_BG, COLOR_PANEL_ACTION_DISABLED_TEXT, COLOR_PANEL_ACTION_HOVER_BG,
    COLOR_PANEL_ACTION_TEXT, COLOR_VIDEO_BG, COLOR_VIDEO_BORDER,
    COLOR_VIDEO_TITLE, FONT_SIZE_CLOSE_BUTTON, FONT_SIZE_VIDEO_TITLE,
    PANEL_ACTION_BUTTON_HEIGHT, PANEL_ACTION_BUTTON_PADDING_H, PANEL_ACTION_BUTTON_RADIUS,
    PANEL_BODY_MARGIN, PANEL_BORDER_MARGIN, PANEL_BORDER_RADIUS,
    PANEL_BORDER_WIDTH, PANEL_CLOSE_BUTTON_RADIUS, PANEL_CLOSE_BUTTON_SIZE,
    PANEL_CLOSE_GLYPH, PANEL_HEADER_HEIGHT, PANEL_HEADER_SPACING,
    PANEL_TITLE_MAX_LENGTH,
)


class HeaderDragFilter(QObject):
    def __init__(self, panel) -> None:
        super().__init__(panel)
        self._panel = panel

    def eventFilter(self, watched, event):
        return self._panel.handle_header_event(event)


class FloatingPanel(QFrame):
    panel_closed = pyqtSignal()

    def __init__(
        self,
        parent=None,
        width: int = 380,
        height: int = 240,
        min_width: int = 260,
        min_height: int = 160,
        object_name: str = "floatingPanel",
        border_color: str = COLOR_VIDEO_BORDER,
        background: str = COLOR_VIDEO_BG,
        title_color: str = COLOR_VIDEO_TITLE,
        title: str = "",
    ) -> None:
        super().__init__(parent)

        self._min_width = min_width
        self._min_height = min_height
        self._title_color = title_color

        self.setObjectName(object_name)
        self.setMinimumSize(min_width, min_height)
        self.resize(width, height)
        self.setMouseTracking(True)
        self.setStyleSheet(f"""
            QFrame#{object_name} {{
                background-color: {background};
                border: {PANEL_BORDER_WIDTH}px solid {border_color};
                border-radius: {PANEL_BORDER_RADIUS}px;
            }}
        """)

        self._resizing = False
        self._moving = False
        self._resize_edges = {"right": False, "bottom": False}
        self._press_pos = QPoint()
        self._press_geom = QRect()

        self._outer = QVBoxLayout(self)
        self._outer.setContentsMargins(
            PANEL_BODY_MARGIN, PANEL_BODY_MARGIN - 2, PANEL_BODY_MARGIN, PANEL_BODY_MARGIN
        )
        self._outer.setSpacing(2)

        self.header_frame = QFrame(self)
        self.header_frame.setFixedHeight(PANEL_HEADER_HEIGHT)
        self.header_frame.setStyleSheet("background: transparent; border: none;")
        self.header_frame.setCursor(QCursor(Qt.CursorShape.ArrowCursor))

        self._header_filter = HeaderDragFilter(self)
        self.header_frame.installEventFilter(self._header_filter)

        header_layout = QHBoxLayout(self.header_frame)
        header_layout.setContentsMargins(4, 0, 4, 0)
        header_layout.setSpacing(PANEL_HEADER_SPACING)

        self.title_label = QLabel(title, self.header_frame)
        self.title_label.installEventFilter(self._header_filter)
        self.title_label.setStyleSheet(
            f"color: {title_color}; font-weight: bold; font-size: {FONT_SIZE_VIDEO_TITLE}px; border: none;"
        )
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()

        self._actions_layout = QHBoxLayout()
        self._actions_layout.setContentsMargins(0, 0, 0, 0)
        self._actions_layout.setSpacing(PANEL_HEADER_SPACING)
        header_layout.addLayout(self._actions_layout)

        self.close_button = QPushButton(PANEL_CLOSE_GLYPH, self.header_frame)
        self.close_button.setFixedSize(PANEL_CLOSE_BUTTON_SIZE, PANEL_CLOSE_BUTTON_SIZE)
        self.close_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.close_button.setStyleSheet(f"""
            QPushButton {{
                color: {COLOR_CLOSE_BUTTON_TEXT};
                background-color: {COLOR_CLOSE_BUTTON_BG};
                border: none;
                border-radius: {PANEL_CLOSE_BUTTON_RADIUS}px;
                font-size: {FONT_SIZE_CLOSE_BUTTON}px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background-color: {COLOR_CLOSE_BUTTON_HOVER_BG}; }}
        """)
        self.close_button.clicked.connect(self.close_panel)
        header_layout.addWidget(self.close_button)

        self._outer.addWidget(self.header_frame)

    def add_body_widget(self, widget) -> None:
        self._outer.addWidget(widget, stretch=1)

    def make_action_button(self, text: str) -> QPushButton:
        button = QPushButton(text, self.header_frame)
        button.setFixedHeight(PANEL_ACTION_BUTTON_HEIGHT)
        button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        button.setStyleSheet(f"""
            QPushButton {{
                color: {COLOR_PANEL_ACTION_TEXT};
                background-color: {COLOR_PANEL_ACTION_BG};
                border: none;
                border-radius: {PANEL_ACTION_BUTTON_RADIUS}px;
                padding: 0px {PANEL_ACTION_BUTTON_PADDING_H}px;
                font-size: {FONT_SIZE_CLOSE_BUTTON}px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background-color: {COLOR_PANEL_ACTION_HOVER_BG}; }}
            QPushButton:disabled {{ color: {COLOR_PANEL_ACTION_DISABLED_TEXT}; }}
        """)
        self._actions_layout.addWidget(button)
        return button

    def set_title(self, text: str) -> None:
        self.title_label.setText(str(text)[:PANEL_TITLE_MAX_LENGTH].upper())

    def close_panel(self) -> None:
        self._moving = False
        self._resizing = False
        self.hide()
        self.panel_closed.emit()

    def handle_header_event(self, event) -> bool:
        kind = event.type()

        if kind == QEvent.Type.MouseButtonPress:
            if event.button() != Qt.MouseButton.LeftButton:
                return False
            self._begin_move(event.globalPosition().toPoint())
            return True

        if kind == QEvent.Type.MouseMove and self._moving:
            self._continue_move(event.globalPosition().toPoint())
            return True

        if kind == QEvent.Type.MouseButtonRelease and self._moving:
            self._end_drag()
            return True

        return False

    def _begin_move(self, global_pos: QPoint) -> None:
        self._moving = True
        self._resizing = False
        self._press_pos = global_pos
        self._press_geom = self.geometry()
        self.setCursor(QCursor(Qt.CursorShape.SizeAllCursor))

    def _continue_move(self, global_pos: QPoint) -> None:
        self.move(self._press_geom.topLeft() + (global_pos - self._press_pos))

    def _end_drag(self) -> None:
        self._moving = False
        self._resizing = False
        self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))

    def _get_resize_edges(self, pos: QPoint) -> dict:
        rect = self.rect()
        margin = PANEL_BORDER_MARGIN
        return {
            "right": pos.x() >= rect.width() - margin,
            "bottom": pos.y() >= rect.height() - margin,
        }

    def _update_cursor_shape(self, edges: dict) -> None:
        bottom, right = edges["bottom"], edges["right"]
        if bottom and right:
            self.setCursor(QCursor(Qt.CursorShape.SizeFDiagCursor))
        elif right:
            self.setCursor(QCursor(Qt.CursorShape.SizeHorCursor))
        elif bottom:
            self.setCursor(QCursor(Qt.CursorShape.SizeVerCursor))
        else:
            self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))

    def mousePressEvent(self, event) -> None:
        if event.button() != Qt.MouseButton.LeftButton:
            super().mousePressEvent(event)
            return

        edges = self._get_resize_edges(event.pos())

        if any(edges.values()):
            self._resizing = True
            self._moving = False
            self._resize_edges = edges
            self._press_pos = event.globalPosition().toPoint()
            self._press_geom = self.geometry()
            event.accept()
            return

        if event.pos().y() <= PANEL_BODY_MARGIN:
            self._begin_move(event.globalPosition().toPoint())
            event.accept()
            return

        self.on_body_clicked()
        event.accept()

    def mouseMoveEvent(self, event) -> None:
        if self._resizing:
            delta = event.globalPosition().toPoint() - self._press_pos
            new_w = self._press_geom.width()
            new_h = self._press_geom.height()
            if self._resize_edges["right"]:
                new_w = max(self._min_width, new_w + delta.x())
            if self._resize_edges["bottom"]:
                new_h = max(self._min_height, new_h + delta.y())
            self.resize(new_w, new_h)
            event.accept()
            return

        if self._moving:
            self._continue_move(event.globalPosition().toPoint())
            event.accept()
            return

        self._update_cursor_shape(self._get_resize_edges(event.pos()))
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        self._end_drag()
        super().mouseReleaseEvent(event)

    def on_body_clicked(self) -> None:
        return None
