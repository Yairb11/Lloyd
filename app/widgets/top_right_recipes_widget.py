from PyQt6.QtCore import QPoint, QRect, Qt
from PyQt6.QtGui import QCursor
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLayout,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.config import (
    COLOR_RECIPE_BADGE_BG,
    COLOR_RECIPE_BG,
    COLOR_RECIPE_BORDER,
    COLOR_RECIPE_CLOSE_BG,
    COLOR_RECIPE_CLOSE_HOVER_BG,
    COLOR_RECIPE_CLOSE_TEXT,
    COLOR_RECIPE_GARNISH_TEXT,
    COLOR_RECIPE_INGREDIENT_NAME,
    COLOR_RECIPE_INGREDIENT_VALUE,
    COLOR_RECIPE_INGREDIENTS_BG,
    COLOR_RECIPE_STEP_BADGE_BG,
    COLOR_RECIPE_STEP_TEXT,
    COLOR_RECIPE_TITLE,
    FONT_SIZE_RECIPE_BADGE,
    FONT_SIZE_RECIPE_CLOSE_BUTTON,
    FONT_SIZE_RECIPE_GARNISH,
    FONT_SIZE_RECIPE_INGREDIENT,
    FONT_SIZE_RECIPE_STEP,
    FONT_SIZE_RECIPE_STEP_BADGE,
    FONT_SIZE_RECIPE_TITLE,
    OBJECT_NAME_RECIPE_WIDGET,
    RECIPE_POPUP_BORDER_MARGIN,
    RECIPE_POPUP_BORDER_RADIUS,
    RECIPE_POPUP_BORDER_WIDTH,
    RECIPE_POPUP_CLOSE_BUTTON_RADIUS,
    RECIPE_POPUP_CLOSE_BUTTON_SIZE,
    RECIPE_POPUP_CLOSE_GLYPH,
    RECIPE_POPUP_DEFAULT_HEIGHT,
    RECIPE_POPUP_DEFAULT_TITLE,
    RECIPE_POPUP_DEFAULT_WIDTH,
    RECIPE_POPUP_HEADER_HEIGHT,
    RECIPE_POPUP_MIN_HEIGHT,
    RECIPE_POPUP_MIN_WIDTH,
    RECIPE_POPUP_POSITION_OFFSET,
    RECIPE_POPUP_STEP_BADGE_SIZE,
    RECIPE_POPUP_TITLE_MAX_LENGTH,
)


class TopRightRecipyWidget(QFrame):
    def __init__(self, parent=None, width: int = RECIPE_POPUP_DEFAULT_WIDTH, height: int = RECIPE_POPUP_DEFAULT_HEIGHT):
        super().__init__(parent)
        self.setMinimumSize(RECIPE_POPUP_MIN_WIDTH, RECIPE_POPUP_MIN_HEIGHT)
        self.resize(width, height)
        self.setMouseTracking(True)

        self._resizing = False
        self._resize_edges = {"bottom": False, "left": False}
        self._press_pos = QPoint()
        self._press_geom = QRect()

        self.setStyleSheet(f"""
            QFrame#{OBJECT_NAME_RECIPE_WIDGET} {{
                background-color: {COLOR_RECIPE_BG};
                border: {RECIPE_POPUP_BORDER_WIDTH}px solid {COLOR_RECIPE_BORDER};
                border-radius: {RECIPE_POPUP_BORDER_RADIUS}px;
            }}
        """)
        self.setObjectName(OBJECT_NAME_RECIPE_WIDGET)

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(10, 8, 10, 10)
        outer_layout.setSpacing(8)

        self.header_frame = QFrame(self)
        self.header_frame.setFixedHeight(RECIPE_POPUP_HEADER_HEIGHT)
        self.header_frame.setStyleSheet("background: transparent; border: none;")
        header_layout = QHBoxLayout(self.header_frame)
        header_layout.setContentsMargins(2, 0, 2, 0)
        header_layout.setSpacing(4)

        self.title_label = QLabel(RECIPE_POPUP_DEFAULT_TITLE, self.header_frame)
        self.title_label.setStyleSheet(
            f"color: {COLOR_RECIPE_TITLE}; font-weight: bold; "
            f"font-size: {FONT_SIZE_RECIPE_TITLE}px; border: none;"
        )
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()

        close_btn = QPushButton(RECIPE_POPUP_CLOSE_GLYPH, self.header_frame)
        close_btn.setFixedSize(RECIPE_POPUP_CLOSE_BUTTON_SIZE, RECIPE_POPUP_CLOSE_BUTTON_SIZE)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                color: {COLOR_RECIPE_CLOSE_TEXT};
                background-color: {COLOR_RECIPE_CLOSE_BG};
                border: none;
                border-radius: {RECIPE_POPUP_CLOSE_BUTTON_RADIUS}px;
                font-size: {FONT_SIZE_RECIPE_CLOSE_BUTTON}px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background-color: {COLOR_RECIPE_CLOSE_HOVER_BG}; }}
        """)
        close_btn.clicked.connect(self.hide)
        header_layout.addWidget(close_btn)

        outer_layout.addWidget(self.header_frame)

        badge_row = QHBoxLayout()
        badge_row.setSpacing(6)
        self.glass_badge = self._make_badge(badge_row)
        self.technique_badge = self._make_badge(badge_row)
        self.ice_badge = self._make_badge(badge_row)

        self.badge_row_widget = QWidget(self)
        self.badge_row_widget.setLayout(badge_row)
        outer_layout.addWidget(self.badge_row_widget)

        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setStyleSheet("background: transparent; border: none;")
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.content_widget = QWidget()
        content_layout = QVBoxLayout(self.content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(8)

        self.ingredients_card = QFrame(self.content_widget)
        self.ingredients_card.setStyleSheet(
            f"background-color: {COLOR_RECIPE_INGREDIENTS_BG}; border-radius: 6px;"
        )
        self.ingredients_layout = QVBoxLayout(self.ingredients_card)
        self.ingredients_layout.setContentsMargins(10, 8, 10, 8)
        self.ingredients_layout.setSpacing(4)
        content_layout.addWidget(self.ingredients_card)

        self.steps_layout = QVBoxLayout()
        self.steps_layout.setSpacing(8)
        content_layout.addLayout(self.steps_layout)

        self.garnish_label = QLabel(self.content_widget)
        self.garnish_label.setWordWrap(True)
        self.garnish_label.setStyleSheet(
            f"color: {COLOR_RECIPE_GARNISH_TEXT}; font-size: {FONT_SIZE_RECIPE_GARNISH}px; border: none;"
        )
        self.garnish_label.hide()
        content_layout.addWidget(self.garnish_label)

        content_layout.addStretch(1)
        self.scroll_area.setWidget(self.content_widget)
        outer_layout.addWidget(self.scroll_area, stretch=1)

    def _make_badge(self, row: QHBoxLayout) -> QLabel:
        badge = QLabel("", self)
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge.setStyleSheet(f"""
            background-color: {COLOR_RECIPE_BADGE_BG};
            color: {COLOR_RECIPE_TITLE};
            border-radius: 10px;
            padding: 4px 8px;
            font-size: {FONT_SIZE_RECIPE_BADGE}px;
            font-weight: bold;
        """)
        row.addWidget(badge, stretch=1)
        return badge

    def show_recipe(self, data: dict) -> None:
        name = str(data.get("name", RECIPE_POPUP_DEFAULT_TITLE))
        self.title_label.setText(name[:RECIPE_POPUP_TITLE_MAX_LENGTH].upper())

        self.glass_badge.setText(str(data.get("glass_type", "")).replace("_", " ").upper())
        self.technique_badge.setText(str(data.get("technique", "")).upper())
        self.ice_badge.setText(str(data.get("ice", "")).upper())

        self._clear_layout(self.ingredients_layout)
        for ingredient in data.get("ingredients", []) or []:
            self.ingredients_layout.addLayout(self._make_ingredient_row(ingredient))

        self._clear_layout(self.steps_layout)
        for index, step in enumerate(data.get("steps", []) or [], start=1):
            self.steps_layout.addLayout(self._make_step_row(index, str(step)))

        garnish = data.get("garnish")
        if garnish:
            self.garnish_label.setText(f"Garnish: {garnish}")
            self.garnish_label.show()
        else:
            self.garnish_label.hide()

        self._fit_to_content()

        self.show()
        self.raise_()

    def _fit_to_content(self) -> None:
        content_layout = self.content_widget.layout()

        target_width = self.scroll_area.viewport().width()
        if target_width <= 0:
            target_width = self.content_widget.width()

        if content_layout.hasHeightForWidth():
            content_height = content_layout.heightForWidth(target_width)
        else:
            content_height = self.content_widget.sizeHint().height()

        margins = self.layout().contentsMargins()
        spacing = self.layout().spacing()
        chrome_height = (
            margins.top() + margins.bottom()
            + self.header_frame.height()
            + self.badge_row_widget.sizeHint().height()
            + spacing * 2
        )

        desired_height = chrome_height + content_height
        new_height = min(max(desired_height, RECIPE_POPUP_MIN_HEIGHT), self._max_popup_height())
        self.resize(self.width(), new_height)

    def _max_popup_height(self) -> int:
        parent = self.parentWidget()
        if parent is None:
            return RECIPE_POPUP_DEFAULT_HEIGHT
        return max(RECIPE_POPUP_MIN_HEIGHT, parent.height() - 2 * RECIPE_POPUP_POSITION_OFFSET)

    def _make_ingredient_row(self, ingredient: dict) -> QHBoxLayout:
        row = QHBoxLayout()

        name_label = QLabel(str(ingredient.get("name", "")))
        name_label.setStyleSheet(
            f"color: {COLOR_RECIPE_INGREDIENT_NAME}; font-size: {FONT_SIZE_RECIPE_INGREDIENT}px; border: none;"
        )
        row.addWidget(name_label, stretch=1)

        value_label = QLabel(str(ingredient.get("display", "")))
        value_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        value_label.setStyleSheet(
            f"color: {COLOR_RECIPE_INGREDIENT_VALUE}; font-size: {FONT_SIZE_RECIPE_INGREDIENT}px; "
            f"font-weight: bold; border: none;"
        )
        row.addWidget(value_label)
        return row

    def _make_step_row(self, index: int, instruction: str) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(8)

        badge = QLabel(str(index))
        badge.setFixedSize(RECIPE_POPUP_STEP_BADGE_SIZE, RECIPE_POPUP_STEP_BADGE_SIZE)
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge.setStyleSheet(f"""
            background-color: {COLOR_RECIPE_STEP_BADGE_BG};
            color: white;
            font-weight: bold;
            font-size: {FONT_SIZE_RECIPE_STEP_BADGE}px;
            border-radius: {RECIPE_POPUP_STEP_BADGE_SIZE // 2}px;
        """)
        row.addWidget(badge, alignment=Qt.AlignmentFlag.AlignTop)

        text_label = QLabel(instruction)
        text_label.setWordWrap(True)
        text_label.setStyleSheet(
            f"color: {COLOR_RECIPE_STEP_TEXT}; font-size: {FONT_SIZE_RECIPE_STEP}px; border: none;"
        )
        row.addWidget(text_label, stretch=1)
        return row

    def _clear_layout(self, layout: QLayout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            child_widget = item.widget()
            child_layout = item.layout()
            if child_widget is not None:
                child_widget.deleteLater()
            elif child_layout is not None:
                self._clear_layout(child_layout)

    def shutdown(self) -> None:
        self.hide()

    def _get_resize_edges(self, pos: QPoint) -> dict[str, bool]:
        rect = self.rect()
        m = RECIPE_POPUP_BORDER_MARGIN
        return {
            "left": pos.x() <= m,
            "bottom": pos.y() >= rect.height() - m,
        }

    def _update_cursor_shape(self, edges: dict[str, bool]) -> None:
        bottom, left = edges["bottom"], edges["left"]
        if bottom and left:
            self.setCursor(QCursor(Qt.CursorShape.SizeBDiagCursor))
        elif left:
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
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._resizing:
            delta = event.globalPosition().toPoint() - self._press_pos
            geom = self._press_geom
            new_x = geom.x()
            new_w = geom.width()
            new_h = geom.height()

            if self._resize_edges["left"]:
                new_w = max(RECIPE_POPUP_MIN_WIDTH, geom.width() - delta.x())
                new_x = geom.x() + (geom.width() - new_w)
            if self._resize_edges["bottom"]:
                new_h = max(RECIPE_POPUP_MIN_HEIGHT, geom.height() + delta.y())

            self.setGeometry(new_x, geom.y(), new_w, new_h)
            event.accept()
            return

        edges = self._get_resize_edges(event.pos())
        self._update_cursor_shape(edges)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._resizing = False
        self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
        super().mouseReleaseEvent(event)