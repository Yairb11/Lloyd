import os
import sys

from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QCursor
from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer
from PyQt6.QtMultimediaWidgets import QVideoWidget

from app.config import (
    COLOR_VIDEO_PLAYER_BG, OBJECT_NAME_VIDEO_WIDGET, VIDEO_DEFAULT_HEIGHT,
    VIDEO_DEFAULT_TITLE, VIDEO_DEFAULT_WIDTH, VIDEO_MIN_HEIGHT,
    VIDEO_MIN_WIDTH, VIDEO_PLAYER_BORDER_RADIUS,
)
from app.widgets.floating_panel import FloatingPanel


class TopLeftVideoWidget(FloatingPanel):
    def __init__(self, parent=None, width: int = VIDEO_DEFAULT_WIDTH, height: int = VIDEO_DEFAULT_HEIGHT) -> None:
        super().__init__(
            parent=parent,
            width=width,
            height=height,
            min_width=VIDEO_MIN_WIDTH,
            min_height=VIDEO_MIN_HEIGHT,
            object_name=OBJECT_NAME_VIDEO_WIDGET,
            title=VIDEO_DEFAULT_TITLE,
        )

        self._active_video_path: str = ""

        self.video_widget = QVideoWidget(self)
        self.video_widget.setStyleSheet(
            f"border-radius: {VIDEO_PLAYER_BORDER_RADIUS}px; border: none; "
            f"background-color: {COLOR_VIDEO_PLAYER_BG};"
        )
        self.video_widget.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.video_widget.installEventFilter(self)
        self.add_body_widget(self.video_widget)

        self.player = QMediaPlayer(self)
        self.audio_output = QAudioOutput(self)
        self.player.setAudioOutput(self.audio_output)
        self.player.setVideoOutput(self.video_widget)
        self.player.setLoops(QMediaPlayer.Loops.Infinite)

    def show_preparing(self, title: str) -> None:
        self._active_video_path = ""
        self.player.stop()
        self.player.setSource(QUrl())
        self.set_title(title)
        self.show()
        self.raise_()

    def play_video(self, file_path: str, title: str = VIDEO_DEFAULT_TITLE) -> None:
        self._active_video_path = file_path
        self.set_title(title)
        self.player.setSource(QUrl.fromLocalFile(file_path))
        self.show()
        self.raise_()
        self.player.play()

    def close_panel(self) -> None:
        self.player.stop()
        super().close_panel()

    def on_body_clicked(self) -> None:
        self.open_in_external_viewer()

    def open_in_external_viewer(self) -> None:
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
        if watched is self.video_widget and event.type() == event.Type.MouseButtonPress:
            if event.button() == Qt.MouseButton.LeftButton:
                self.open_in_external_viewer()
                return True
        return super().eventFilter(watched, event)
