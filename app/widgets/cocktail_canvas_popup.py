from PyQt6.QtCore import pyqtSignal

from app.config import (
    CANVAS_POPUP_DEFAULT_HEIGHT, CANVAS_POPUP_DEFAULT_TITLE, CANVAS_POPUP_DEFAULT_WIDTH,
    CANVAS_POPUP_EXPORTING_TEXT, CANVAS_POPUP_EXPORT_TEXT, CANVAS_POPUP_MIN_HEIGHT,
    CANVAS_POPUP_MIN_WIDTH, COLOR_CANVAS_POPUP_BORDER, OBJECT_NAME_CANVAS_POPUP,
)
from app.widgets.cocktail_canvas import CocktailCanvas
from app.widgets.floating_panel import FloatingPanel


class CocktailCanvasPopup(FloatingPanel):
    export_requested = pyqtSignal(dict)

    def __init__(
        self,
        parent=None,
        width: int = CANVAS_POPUP_DEFAULT_WIDTH,
        height: int = CANVAS_POPUP_DEFAULT_HEIGHT,
    ) -> None:
        super().__init__(
            parent=parent,
            width=width,
            height=height,
            min_width=CANVAS_POPUP_MIN_WIDTH,
            min_height=CANVAS_POPUP_MIN_HEIGHT,
            object_name=OBJECT_NAME_CANVAS_POPUP,
            border_color=COLOR_CANVAS_POPUP_BORDER,
            title_color=COLOR_CANVAS_POPUP_BORDER,
            title=CANVAS_POPUP_DEFAULT_TITLE,
        )

        self._spec: dict | None = None
        self._exporting: bool = False

        self.export_button = self.make_action_button(CANVAS_POPUP_EXPORT_TEXT)
        self.export_button.clicked.connect(self._on_export_clicked)
        self.export_button.setEnabled(False)

        self.canvas = CocktailCanvas(self)
        self.canvas.animation_started.connect(self._on_animation_started)
        self.add_body_widget(self.canvas)

    def play(self, spec: dict) -> None:
        self._spec = dict(spec)
        self._set_export_idle()
        self.canvas.play_spec(self._spec)
        self.show()
        self.raise_()

    def stop(self) -> None:
        self.canvas.stop()
        self._spec = None
        self.export_button.setEnabled(False)

    def export_settled(self) -> None:
        if self._spec is not None:
            self._set_export_idle()

    def _set_export_idle(self) -> None:
        self._exporting = False
        self.export_button.setText(CANVAS_POPUP_EXPORT_TEXT)
        self.export_button.setEnabled(True)

    def _on_animation_started(self, name: str) -> None:
        self.set_title(name or CANVAS_POPUP_DEFAULT_TITLE)

    def _on_export_clicked(self) -> None:
        if self._spec is None or self._exporting:
            return
        self._exporting = True
        self.export_button.setText(CANVAS_POPUP_EXPORTING_TEXT)
        self.export_button.setEnabled(False)
        self.export_requested.emit(dict(self._spec))

    def close_panel(self) -> None:
        self.canvas.stop()
        super().close_panel()
