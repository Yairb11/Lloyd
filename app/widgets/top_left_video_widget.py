import os
import sys
from PyQt6.QtCore import QPoint, QRect, Qt, QUrl
from PyQt6.QtGui import QCursor
from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer
from PyQt6.QtMultimediaWidgets import QVideoWidget
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

from app.config import (
    COLOR_CLOSE_BUTTON_BG,
    COLOR_CLOSE_BUTTON_HOVER_BG,
    COLOR_CLOSE_BUTTON_TEXT,
    COLOR_VIDEO_BG,
    COLOR_VIDEO_BORDER,
    COLOR_VIDEO_PLAYER_BG,
    COLOR_VIDEO_TITLE,
    FONT_SIZE_CLOSE_BUTTON,
    FONT_SIZE_VIDEO_TITLE,
    OBJECT_NAME_VIDEO_WIDGET,
    VIDEO_BORDER_MARGIN,
    VIDEO_BORDER_RADIUS,
    VIDEO_BORDER_WIDTH,
    VIDEO_CLOSE_BUTTON_RADIUS,
    VIDEO_CLOSE_BUTTON_SIZE,
    VIDEO_CLOSE_GLYPH,
    VIDEO_DEFAULT_HEIGHT,
    VIDEO_DEFAULT_TITLE,
    VIDEO_DEFAULT_WIDTH,
    VIDEO_HEADER_HEIGHT,
    VIDEO_MIN_HEIGHT,
    VIDEO_MIN_WIDTH,
    VIDEO_PLAYER_BORDER_RADIUS,
    VIDEO_TITLE_MAX_LENGTH,
)


class TopLeftVideoWidget(QFrame):
    def __init__(self, parent=None, width: int = VIDEO_DEFAULT_WIDTH, height: int = VIDEO_DEFAULT_HEIGHT):
        super().__init__(parent)
        self.setMinimumSize(VIDEO_MIN_WIDTH, VIDEO_MIN_HEIGHT)
        self.resize(width, height)
        self.setMouseTracking(True)

        self._active_video_path: str = ""
        self._resizing = False
        self._resize_edges = {"bottom": False, "right": False}
        self._press_pos = QPoint()
        self._press_geom = QRect()

        self.setStyleSheet(f"""
            QFrame#{OBJECT_NAME_VIDEO_WIDGET} {{
                background-color: {COLOR_VIDEO_BG};
                border: {VIDEO_BORDER_WIDTH}px solid {COLOR_VIDEO_BORDER};
                border-radius: {VIDEO_BORDER_RADIUS}px;
            }}
        """)
        self.setObjectName(OBJECT_NAME_VIDEO_WIDGET)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 4, 6, 6)
        layout.setSpacing(2)

        self.header_frame = QFrame(self)
        self.header_frame.setFixedHeight(VIDEO_HEADER_HEIGHT)
        self.header_frame.setStyleSheet("background: transparent; border: none;")
        header_layout = QHBoxLayout(self.header_frame)
        header_layout.setContentsMargins(4, 0, 4, 0)
        header_layout.setSpacing(4)

        self.title_label = QLabel(VIDEO_DEFAULT_TITLE, self.header_frame)
        self.title_label.setStyleSheet(f"color: {COLOR_VIDEO_TITLE}; font-weight: bold; font-size: {FONT_SIZE_VIDEO_TITLE}px; border: none;")
        header_layout.addWidget(self.title_label)

        header_layout.addStretch()

        close_btn = QPushButton(VIDEO_CLOSE_GLYPH, self.header_frame)
        close_btn.setFixedSize(VIDEO_CLOSE_BUTTON_SIZE, VIDEO_CLOSE_BUTTON_SIZE)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                color: {COLOR_CLOSE_BUTTON_TEXT};
                background-color: {COLOR_CLOSE_BUTTON_BG};
                border: none;
                border-radius: {VIDEO_CLOSE_BUTTON_RADIUS}px;
                font-size: {FONT_SIZE_CLOSE_BUTTON}px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background-color: {COLOR_CLOSE_BUTTON_HOVER_BG}; }}
        """)
        close_btn.clicked.connect(self.close_preview)
        header_layout.addWidget(close_btn)

        layout.addWidget(self.header_frame)

        self.video_widget = QVideoWidget(self)
        self.video_widget.setStyleSheet(f"border-radius: {VIDEO_PLAYER_BORDER_RADIUS}px; border: none; background-color: {COLOR_VIDEO_PLAYER_BG};")
        self.video_widget.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.video_widget.installEventFilter(self)
        layout.addWidget(self.video_widget, stretch=1)

        self.player = QMediaPlayer(self)
        self.audio_output = QAudioOutput(self)
        self.player.setAudioOutput(self.audio_output)
        self.player.setVideoOutput(self.video_widget)
        self.player.mediaStatusChanged.connect(self._on_status_changed)

    def _on_status_changed(self, status):
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            self.player.setPosition(0)
            self.player.play()

    def show_preparing(self, title: str) -> None:
        self._active_video_path = ""
        self.player.stop()
        self.player.setSource(QUrl())
        self.title_label.setText(title[:VIDEO_TITLE_MAX_LENGTH].upper())
        self.show()
        self.raise_()

    def play_video(self, file_path: str, title: str = VIDEO_DEFAULT_TITLE):
        self._active_video_path = file_path
        self.title_label.setText(title[:VIDEO_TITLE_MAX_LENGTH].upper())
        self.player.setSource(QUrl.fromLocalFile(file_path))
        self.show()
        self.raise_()
        self.player.play()

    def close_preview(self):
        self.player.stop()
        self.hide()

    def open_in_external_viewer(self):
        if not self._active_video_path or not os.path.exists(self._active_video_path):
            return
        self.player.pause()
        path = self._active_video_path
        if sys.platform == "win32":
            os.startfile(path)
        elif sys.platform == "darwin":
            os.system(f'open "{path}"')
        else:
            os.system(f'xdg-open "{path}"')

    def eventFilter(self, watched, event):
        if watched == self.video_widget and event.type() == event.Type.MouseButtonPress:
            if event.button() == Qt.MouseButton.LeftButton:
                self.open_in_external_viewer()
                return True
        return super().eventFilter(watched, event)

    def _get_resize_edges(self, pos: QPoint) -> dict[str, bool]:
        rect = self.rect()
        m = VIDEO_BORDER_MARGIN
        return {
            "right": pos.x() >= rect.width() - m,
            "bottom": pos.y() >= rect.height() - m,
        }

    def _update_cursor_shape(self, edges: dict[str, bool]):
        bottom, right = edges["bottom"], edges["right"]
        if bottom and right:
            self.setCursor(QCursor(Qt.CursorShape.SizeFDiagCursor))
        elif right:
            self.setCursor(QCursor(Qt.CursorShape.SizeHorCursor))
        elif bottom:
            self.setCursor(QCursor(Qt.CursorShape.SizeVerCursor))
        else:
            self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            edges = self._get_resize_edges(event.pos())
            if any(edges.values()):
                self._resizing = True
                self._resize_edges = edges
                self._press_pos = event.globalPosition().toPoint()
                self._press_geom = self.geometry()
                event.accept()
                return
            self.open_in_external_viewer()
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._resizing:
            delta = event.globalPosition().toPoint() - self._press_pos
            new_w = self._press_geom.width()
            new_h = self._press_geom.height()

            if self._resize_edges["right"]:
                new_w = max(VIDEO_MIN_WIDTH, new_w + delta.x())
            if self._resize_edges["bottom"]:
                new_h = max(VIDEO_MIN_HEIGHT, new_h + delta.y())

            self.resize(new_w, new_h)
            event.accept()
            return

        edges = self._get_resize_edges(event.pos())
        self._update_cursor_shape(edges)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._resizing = False
        self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
        super().mouseReleaseEvent(event)
