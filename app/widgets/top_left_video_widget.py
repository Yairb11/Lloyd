import os
import sys

from PyQt6.QtCore import QUrl, Qt, QPoint, QRect
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

class TopLeftVideoWidget(QFrame):
    BORDER_MARGIN = 8
    MIN_WIDTH = 260
    MIN_HEIGHT = 160

    def __init__(self, parent=None, width: int = 380, height: int = 240):
        super().__init__(parent)
        self.setMinimumSize(self.MIN_WIDTH, self.MIN_HEIGHT)
        self.resize(width, height)
        self.setMouseTracking(True)

        self._active_video_path: str = ""
        self._resizing = False
        self._resize_edges = {"bottom": False, "right": False}
        self._press_pos = QPoint()
        self._press_geom = QRect()

        self.setStyleSheet("""
            QFrame#TopLeftVideoWidget {
                background-color: #0b0f19;
                border: 2px solid #00E5FF;
                border-radius: 8px;
            }
        """)
        self.setObjectName("TopLeftVideoWidget")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 4, 6, 6)
        layout.setSpacing(2)

        self.header_frame = QFrame(self)
        self.header_frame.setFixedHeight(22)
        self.header_frame.setStyleSheet("background: transparent; border: none;")
        header_layout = QHBoxLayout(self.header_frame)
        header_layout.setContentsMargins(4, 0, 4, 0)
        header_layout.setSpacing(4)

        self.title_label = QLabel("ANIMATION PREVIEW", self.header_frame)
        self.title_label.setStyleSheet("color: #00E5FF; font-weight: bold; font-size: 11px; border: none;")
        header_layout.addWidget(self.title_label)

        header_layout.addStretch()

        close_btn = QPushButton("✕", self.header_frame)
        close_btn.setFixedSize(16, 16)
        close_btn.setStyleSheet("""
            QPushButton {
                color: #FFFFFF;
                background-color: #C62828;
                border: none;
                border-radius: 8px;
                font-size: 9px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #E53935; }
        """)
        close_btn.clicked.connect(self.close_preview)
        header_layout.addWidget(close_btn)

        layout.addWidget(self.header_frame)

        self.video_widget = QVideoWidget(self)
        self.video_widget.setStyleSheet("border-radius: 4px; border: none; background-color: #000000;")
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

    def play_video(self, file_path: str, title: str = "RECIPE VISUALIZATION"):
        self._active_video_path = file_path
        self.title_label.setText(title[:30].upper())
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
        m = self.BORDER_MARGIN
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
                new_w = max(self.MIN_WIDTH, new_w + delta.x())
            if self._resize_edges["bottom"]:
                new_h = max(self.MIN_HEIGHT, new_h + delta.y())

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
