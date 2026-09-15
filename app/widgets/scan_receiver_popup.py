import io
import threading
from pathlib import Path
from typing import TYPE_CHECKING
import qrcode
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QVBoxLayout,
    QWidget,
)

from app.config import (
    COLOR_VIDEO_BG,
    COLOR_VIDEO_TITLE,
    PHONE_SCAN_CANCELLED_MESSAGE,
    PHONE_SCAN_INSTRUCTIONS_FONT_SIZE,
    PHONE_SCAN_INSTRUCTIONS_TEXT,
    PHONE_SCAN_MAIN_MARGIN,
    PHONE_SCAN_MAIN_SPACING,
    PHONE_SCAN_PANEL_BG,
    PHONE_SCAN_PANEL_BORDER,
    PHONE_SCAN_PANEL_BORDER_RADIUS,
    PHONE_SCAN_PANEL_MARGIN,
    PHONE_SCAN_PORT,
    PHONE_SCAN_PREVIEW_FONT_SIZE,
    PHONE_SCAN_PREVIEW_PLACEHOLDER_COLOR,
    PHONE_SCAN_PREVIEW_PLACEHOLDER_TEXT,
    PHONE_SCAN_QR_BACK_COLOR,
    PHONE_SCAN_QR_BORDER,
    PHONE_SCAN_QR_BOX_SIZE,
    PHONE_SCAN_QR_FILL_COLOR,
    PHONE_SCAN_STATUS_FONT_SIZE,
    PHONE_SCAN_STATUS_WAITING_TEXT,
    PHONE_SCAN_SUBTEXT_COLOR,
    PHONE_SCAN_TITLE_FONT_SIZE,
    PHONE_SCAN_TITLE_TEXT,
    PHONE_SCAN_URL_FONT_SIZE,
    PHONE_SCAN_URL_TEXT_COLOR,
    PHONE_SCAN_WINDOW_HEIGHT,
    PHONE_SCAN_WINDOW_TITLE,
    PHONE_SCAN_WINDOW_WIDTH,
)
from app.helpers.phone_upload_handle import (
    PhoneUploadHandler,
    PhoneUploadServer,
    ServerBridge,
    get_local_ip,
)
from app.threads.phone_server_worker import PhoneServerWorker

if TYPE_CHECKING:
    from app.threads.agent import Agent


class ScanReceiverPopup(QMainWindow):
    def __init__(self, agent: "Agent", done_event: threading.Event, parent=None) -> None:
        super().__init__(parent)
        self.agent = agent
        self._done_event = done_event
        self._received_path: Path | None = None
        self._cleaned_up = False

        self.local_ip = get_local_ip()
        self.server_url = f"http://{self.local_ip}:{PHONE_SCAN_PORT}"

        self.bridge = ServerBridge()
        self.bridge.image_received.connect(self._on_image_received)

        self.httpd = PhoneUploadServer(
            ("0.0.0.0", PHONE_SCAN_PORT), PhoneUploadHandler, bridge=self.bridge
        )
        self.phone_worker = PhoneServerWorker(self.httpd)
        self.agent._spawn_child(self.phone_worker)
        self.phone_worker.finished.connect(self.close)

        self.setWindowTitle(PHONE_SCAN_WINDOW_TITLE)
        self.resize(PHONE_SCAN_WINDOW_WIDTH, PHONE_SCAN_WINDOW_HEIGHT)
        self.setStyleSheet(f"background-color: {COLOR_VIDEO_BG};")

        self._init_ui()
        self.phone_worker.start()

    def _init_ui(self) -> None:
        central = QWidget(self)
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(
            PHONE_SCAN_MAIN_MARGIN,
            PHONE_SCAN_MAIN_MARGIN,
            PHONE_SCAN_MAIN_MARGIN,
            PHONE_SCAN_MAIN_MARGIN,
        )
        main_layout.setSpacing(PHONE_SCAN_MAIN_SPACING)

        panel_style = (
            f"background: {PHONE_SCAN_PANEL_BG}; border: 1px solid {PHONE_SCAN_PANEL_BORDER}; "
            f"border-radius: {PHONE_SCAN_PANEL_BORDER_RADIUS}px;"
        )

        left_box = QFrame(self)
        left_box.setStyleSheet(panel_style)
        left_layout = QVBoxLayout(left_box)
        left_layout.setContentsMargins(
            PHONE_SCAN_PANEL_MARGIN,
            PHONE_SCAN_PANEL_MARGIN,
            PHONE_SCAN_PANEL_MARGIN,
            PHONE_SCAN_PANEL_MARGIN,
        )
        left_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title = QLabel(PHONE_SCAN_TITLE_TEXT, left_box)
        title.setStyleSheet(
            f"color: {COLOR_VIDEO_TITLE}; font-weight: bold; "
            f"font-size: {PHONE_SCAN_TITLE_FONT_SIZE}px; border: none;"
        )
        left_layout.addWidget(title, alignment=Qt.AlignmentFlag.AlignCenter)

        instructions = QLabel(PHONE_SCAN_INSTRUCTIONS_TEXT, left_box)
        instructions.setStyleSheet(
            f"color: {PHONE_SCAN_SUBTEXT_COLOR}; font-size: {PHONE_SCAN_INSTRUCTIONS_FONT_SIZE}px; border: none;"
        )
        left_layout.addWidget(instructions, alignment=Qt.AlignmentFlag.AlignCenter)

        qr = qrcode.QRCode(box_size=PHONE_SCAN_QR_BOX_SIZE, border=PHONE_SCAN_QR_BORDER)
        qr.add_data(self.server_url)
        qr.make(fit=True)
        img = qr.make_image(fill_color=PHONE_SCAN_QR_FILL_COLOR, back_color=PHONE_SCAN_QR_BACK_COLOR)

        buffer = io.BytesIO()
        img.save(buffer, format="PNG")

        qr_pixmap = QPixmap()
        qr_pixmap.loadFromData(buffer.getvalue())

        qr_label = QLabel(left_box)
        qr_label.setPixmap(qr_pixmap)
        qr_label.setStyleSheet("border: none; margin: 10px 0;")
        left_layout.addWidget(qr_label, alignment=Qt.AlignmentFlag.AlignCenter)

        url_label = QLabel(self.server_url, left_box)
        url_label.setStyleSheet(
            f"color: {PHONE_SCAN_URL_TEXT_COLOR}; font-family: monospace; "
            f"font-size: {PHONE_SCAN_URL_FONT_SIZE}px; font-weight: bold; border: none;"
        )
        left_layout.addWidget(url_label, alignment=Qt.AlignmentFlag.AlignCenter)

        main_layout.addWidget(left_box, 1)

        right_box = QFrame(self)
        right_box.setStyleSheet(panel_style)
        right_layout = QVBoxLayout(right_box)
        right_layout.setContentsMargins(
            PHONE_SCAN_PANEL_MARGIN,
            PHONE_SCAN_PANEL_MARGIN,
            PHONE_SCAN_PANEL_MARGIN,
            PHONE_SCAN_PANEL_MARGIN,
        )

        self.status_header = QLabel(PHONE_SCAN_STATUS_WAITING_TEXT, right_box)
        self.status_header.setStyleSheet(
            f"color: {COLOR_VIDEO_TITLE}; font-weight: bold; "
            f"font-size: {PHONE_SCAN_STATUS_FONT_SIZE}px; border: none;"
        )
        right_layout.addWidget(self.status_header)

        self.preview_label = QLabel(PHONE_SCAN_PREVIEW_PLACEHOLDER_TEXT, right_box)
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setStyleSheet(
            f"color: {PHONE_SCAN_PREVIEW_PLACEHOLDER_COLOR}; "
            f"border: 2px dashed {PHONE_SCAN_PANEL_BORDER}; border-radius: 6px; "
            f"font-size: {PHONE_SCAN_PREVIEW_FONT_SIZE}px;"
        )
        right_layout.addWidget(self.preview_label, stretch=1)

        main_layout.addWidget(right_box, 1)

    def _on_image_received(self, file_path: str) -> None:
        if self._cleaned_up or self._received_path is not None:
            return

        self._received_path = Path(file_path)
        self.agent._scan_result_path = str(self._received_path)

        self._cleaned_up = True
        self.phone_worker.request_stop()
        self._done_event.set()
        self.close()

    def closeEvent(self, event) -> None:
        if not self._cleaned_up:
            self._cleaned_up = True
            self.phone_worker.request_stop()
            self.agent._on_scan_failure(PHONE_SCAN_CANCELLED_MESSAGE)
            self._done_event.set()
        super().closeEvent(event)