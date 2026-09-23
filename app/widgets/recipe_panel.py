import html
from typing import Any

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QGuiApplication
from PyQt6.QtWidgets import (
    QFrame, QGridLayout, QHBoxLayout,
    QLabel, QLayout, QScrollArea,
    QVBoxLayout, QWidget,
)

from app.config import (
    HUD_POSITION_OFFSET, OBJECT_NAME_RECIPE_AMOUNT, OBJECT_NAME_RECIPE_AMOUNT_TOP_UP,
    OBJECT_NAME_RECIPE_BADGE, OBJECT_NAME_RECIPE_DIVIDER, OBJECT_NAME_RECIPE_INGREDIENT_NAME,
    OBJECT_NAME_RECIPE_SCROLL, OBJECT_NAME_RECIPE_SECTION_LINE, OBJECT_NAME_RECIPE_STEP_BODY,
    OBJECT_NAME_RECIPE_STEP_NUMBER, OBJECT_NAME_RECIPE_TABLE, OBJECT_NAME_RECIPE_TITLE,
    OBJECT_NAME_RECIPE_WIDGET, PANEL_RESIZE_SIDE_LEFT, RECIPE_CARD_BADGE_HEIGHT,
    RECIPE_CARD_BADGE_SPACING, RECIPE_CARD_DIVIDER_HEIGHT, RECIPE_CARD_PIP_SIZE,
    RECIPE_CARD_SECTION_GAP, RECIPE_CARD_SECTION_LINE_HEIGHT, RECIPE_CARD_STEP_COLUMN_SPACING,
    RECIPE_CARD_STEP_NUMBER_WIDTH, RECIPE_CARD_STEP_SPACING, RECIPE_CARD_TABLE_COLUMN_SPACING,
    RECIPE_CARD_TABLE_PADDING_H, RECIPE_CARD_TABLE_PADDING_V, RECIPE_CARD_TABLE_ROW_SPACING,
    RECIPE_CARD_TITLE_SPACING, RECIPE_POPUP_DEFAULT_HEIGHT, RECIPE_POPUP_DEFAULT_WIDTH,
    RECIPE_POPUP_MAX_SCREEN_RATIO, RECIPE_POPUP_MIN_HEIGHT, RECIPE_POPUP_MIN_WIDTH,
    RECIPE_STEP_BODY_HTML, RECIPE_STEP_LINE_HEIGHT_PERCENT, RECIPE_TITLE_HTML,
    SCROLLBAR_WIDTH,
)
from app.widget_helpers.recipe_style import build_pip_style, build_recipe_stylesheet
from app.widgets import recipe_content
from app.widgets.floating_panel import FloatingPanel

_INGREDIENT_COLUMN_PIP: int = 0
_INGREDIENT_COLUMN_NAME: int = 1
_INGREDIENT_COLUMN_AMOUNT: int = 2
_INGREDIENT_COLUMN_SPAN: int = 3
_EMPTY_PANEL_TITLE: str = ""


class TopRightRecipyWidget(FloatingPanel):
    def __init__(self, parent=None, width: int = RECIPE_POPUP_DEFAULT_WIDTH, height: int = RECIPE_POPUP_DEFAULT_HEIGHT):
        super().__init__(
            parent=parent,
            width=width,
            height=height,
            min_width=RECIPE_POPUP_MIN_WIDTH,
            min_height=RECIPE_POPUP_MIN_HEIGHT,
            object_name=OBJECT_NAME_RECIPE_WIDGET,
            title=_EMPTY_PANEL_TITLE,
            resize_side=PANEL_RESIZE_SIDE_LEFT,
        )

        self.scroll_area = QScrollArea(self)
        self.scroll_area.setObjectName(OBJECT_NAME_RECIPE_SCROLL)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.add_body_widget(self.scroll_area)

        self.content_widget = QWidget()
        content_layout = QVBoxLayout(self.content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(RECIPE_CARD_SECTION_GAP)

        self.title_section = QWidget(self.content_widget)
        title_layout = QVBoxLayout(self.title_section)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(RECIPE_CARD_TITLE_SPACING)

        self.recipe_title_label = QLabel(_EMPTY_PANEL_TITLE, self.title_section)
        self.recipe_title_label.setObjectName(OBJECT_NAME_RECIPE_TITLE)
        self.recipe_title_label.setTextFormat(Qt.TextFormat.RichText)
        self.recipe_title_label.setWordWrap(True)
        self.recipe_title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_layout.addWidget(self.recipe_title_label)

        self.badge_row = QHBoxLayout()
        self.badge_row.setContentsMargins(0, 0, 0, 0)
        self.badge_row.setSpacing(RECIPE_CARD_BADGE_SPACING)
        title_layout.addLayout(self.badge_row)

        content_layout.addWidget(self.title_section)

        self.title_section_line = self._make_section_line()
        content_layout.addWidget(self.title_section_line)

        self.ingredients_table = QFrame(self.content_widget)
        self.ingredients_table.setObjectName(OBJECT_NAME_RECIPE_TABLE)
        self.ingredients_layout = QGridLayout(self.ingredients_table)
        self.ingredients_layout.setContentsMargins(
            RECIPE_CARD_TABLE_PADDING_H, RECIPE_CARD_TABLE_PADDING_V,
            RECIPE_CARD_TABLE_PADDING_H, RECIPE_CARD_TABLE_PADDING_V,
        )
        self.ingredients_layout.setHorizontalSpacing(RECIPE_CARD_TABLE_COLUMN_SPACING)
        self.ingredients_layout.setVerticalSpacing(RECIPE_CARD_TABLE_ROW_SPACING)
        self.ingredients_layout.setColumnStretch(_INGREDIENT_COLUMN_NAME, 1)
        content_layout.addWidget(self.ingredients_table)

        self.ingredients_section_line = self._make_section_line()
        content_layout.addWidget(self.ingredients_section_line)

        self.steps_layout = QVBoxLayout()
        self.steps_layout.setContentsMargins(0, 0, 0, 0)
        self.steps_layout.setSpacing(RECIPE_CARD_STEP_SPACING)
        content_layout.addLayout(self.steps_layout)

        content_layout.addStretch(1)
        self.scroll_area.setWidget(self.content_widget)

        self.setStyleSheet(self.styleSheet() + build_recipe_stylesheet())

    def show_recipe(self, data: dict[str, Any]) -> None:
        self._populate(data)
        self._fit_to_content()
        self.show()
        self.raise_()

    def shutdown(self) -> None:
        self.hide()

    def _populate(self, data: dict[str, Any]) -> None:
        self.recipe_title_label.setText(
            RECIPE_TITLE_HTML.format(text=html.escape(recipe_content.card_title(data)))
        )

        self._clear_layout(self.badge_row)
        self.badge_row.addStretch(1)
        for label in recipe_content.badge_labels(data):
            self.badge_row.addWidget(self._make_badge(label))
        self.badge_row.addStretch(1)

        ingredients = data.get("ingredients") or []
        self._rebuild_ingredients(ingredients)
        self.ingredients_table.setVisible(bool(ingredients))
        self.ingredients_section_line.setVisible(bool(ingredients))

        self._clear_layout(self.steps_layout)
        for index, step in enumerate(data.get("steps") or [], start=1):
            self.steps_layout.addWidget(self._make_step_row(index, step))

        self.scroll_area.verticalScrollBar().setValue(0)

    def _make_badge(self, text: str) -> QLabel:
        badge = QLabel(text)
        badge.setObjectName(OBJECT_NAME_RECIPE_BADGE)
        badge.setFixedHeight(RECIPE_CARD_BADGE_HEIGHT)
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        return badge

    def _rebuild_ingredients(self, ingredients: list[dict[str, Any]]) -> None:
        self._clear_layout(self.ingredients_layout)

        for index, ingredient in enumerate(ingredients):
            row = index * 2
            if index:
                self.ingredients_layout.addWidget(
                    self._make_divider(), row - 1, _INGREDIENT_COLUMN_PIP, 1, _INGREDIENT_COLUMN_SPAN
                )

            pip = QLabel(self.ingredients_table)
            pip.setFixedSize(RECIPE_CARD_PIP_SIZE, RECIPE_CARD_PIP_SIZE)
            pip.setStyleSheet(build_pip_style(recipe_content.pip_color(ingredient)))
            self.ingredients_layout.addWidget(
                pip, row, _INGREDIENT_COLUMN_PIP, Qt.AlignmentFlag.AlignVCenter
            )

            name_label = QLabel(str(ingredient.get("name", "")), self.ingredients_table)
            name_label.setObjectName(OBJECT_NAME_RECIPE_INGREDIENT_NAME)
            self.ingredients_layout.addWidget(name_label, row, _INGREDIENT_COLUMN_NAME)

            amount_label = QLabel(recipe_content.amount_label(ingredient), self.ingredients_table)
            amount_label.setObjectName(
                OBJECT_NAME_RECIPE_AMOUNT_TOP_UP
                if recipe_content.is_top_up(ingredient)
                else OBJECT_NAME_RECIPE_AMOUNT
            )
            self.ingredients_layout.addWidget(
                amount_label, row, _INGREDIENT_COLUMN_AMOUNT,
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
            )

    def _make_divider(self) -> QFrame:
        divider = QFrame()
        divider.setObjectName(OBJECT_NAME_RECIPE_DIVIDER)
        divider.setFixedHeight(RECIPE_CARD_DIVIDER_HEIGHT)
        return divider

    def _make_section_line(self) -> QFrame:
        line = QFrame(self.content_widget)
        line.setObjectName(OBJECT_NAME_RECIPE_SECTION_LINE)
        line.setFixedHeight(RECIPE_CARD_SECTION_LINE_HEIGHT)
        return line

    def _make_step_row(self, index: int, step: dict[str, Any]) -> QWidget:
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(RECIPE_CARD_STEP_COLUMN_SPACING)

        number_label = QLabel(recipe_content.step_number(index), row)
        number_label.setObjectName(OBJECT_NAME_RECIPE_STEP_NUMBER)
        number_label.setFixedWidth(RECIPE_CARD_STEP_NUMBER_WIDTH)
        layout.addWidget(number_label, 0, Qt.AlignmentFlag.AlignTop)

        instruction_label = QLabel(row)
        instruction_label.setObjectName(OBJECT_NAME_RECIPE_STEP_BODY)
        instruction_label.setTextFormat(Qt.TextFormat.RichText)
        instruction_label.setWordWrap(True)
        instruction_label.setText(
            RECIPE_STEP_BODY_HTML.format(
                percent=RECIPE_STEP_LINE_HEIGHT_PERCENT,
                text=html.escape(recipe_content.instruction_text(step)),
            )
        )
        layout.addWidget(instruction_label, 1)

        return row

    def _clear_layout(self, layout: QLayout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            child_widget = item.widget()
            child_layout = item.layout()
            if child_widget is not None:
                child_widget.setParent(None)
                child_widget.deleteLater()
            elif child_layout is not None:
                self._clear_layout(child_layout)

    def _fit_to_content(self) -> None:
        chrome_height = self._chrome_height()
        max_height = self._max_popup_height()
        content_width = self._content_width()

        desired_height = chrome_height + self._content_height(content_width)

        if desired_height > max_height:
            desired_height = chrome_height + self._content_height(content_width - SCROLLBAR_WIDTH)

        new_height = min(max(desired_height, RECIPE_POPUP_MIN_HEIGHT), max_height)
        self.resize(self.width(), new_height)

    def _chrome_height(self) -> int:
        margins = self.layout().contentsMargins()
        return (
            margins.top() + margins.bottom()
            + self.header_frame.height()
            + self.layout().spacing()
        )

    def _content_width(self) -> int:
        width = self.scroll_area.viewport().width()
        if width <= 0:
            width = self.content_widget.width()
        return width

    def _content_height(self, width: int) -> int:
        content_layout = self.content_widget.layout()
        if width > 0 and content_layout.hasHeightForWidth():
            return content_layout.heightForWidth(width)
        return self.content_widget.sizeHint().height()

    def _max_popup_height(self) -> int:
        limits = []

        screen = self.screen() or QGuiApplication.primaryScreen()
        if screen is not None:
            limits.append(int(screen.availableGeometry().height() * RECIPE_POPUP_MAX_SCREEN_RATIO))

        parent = self.parentWidget()
        if parent is not None:
            limits.append(parent.height() - 2 * HUD_POSITION_OFFSET)

        if not limits:
            return RECIPE_POPUP_DEFAULT_HEIGHT
        return max(RECIPE_POPUP_MIN_HEIGHT, min(limits))