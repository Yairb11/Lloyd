from app.config import (
    CHAT_BUBBLE_PADDING, CHAT_BUBBLE_RADIUS, COLOR_ACCENT,
    COLOR_BG, COLOR_BORDER, COLOR_BUBBLE_AGENT_BG,
    COLOR_BUBBLE_TEXT, COLOR_BUBBLE_USER_BG, COLOR_CANVAS_BG,
    COLOR_INPUT_BG, COLOR_MIC_ACTIVE, COLOR_PANEL_BG,
    COLOR_SCROLLBAR_HANDLE, COLOR_SCROLLBAR_HANDLE_HOVER, COLOR_SCROLLBAR_TRACK,
    COLOR_STOP_ACTIVE, COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY,
    FONT_FAMILY, FONT_SIZE_NORMAL, MUTE_BUTTON_RADIUS,
    OBJECT_NAME_AGENT_BUBBLE, OBJECT_NAME_CANVAS_PANEL, OBJECT_NAME_CHAT_HISTORY,
    OBJECT_NAME_CHAT_PANEL, OBJECT_NAME_MIC_TOGGLE_BUTTON, OBJECT_NAME_MUTE_BUTTON,
    OBJECT_NAME_SEND_BUTTON, OBJECT_NAME_USER_BUBBLE, OBJECT_NAME_VOLUME_POPUP,
    OBJECT_NAME_VOLUME_SLIDER, SCROLLBAR_HANDLE_MIN_HEIGHT, SCROLLBAR_HANDLE_RADIUS,
    SCROLLBAR_WIDTH, STYLE_BORDER_WIDTH, STYLE_BUTTON_BORDER_RADIUS,
    STYLE_BUTTON_PADDING_H, STYLE_BUTTON_PADDING_V, STYLE_INPUT_BORDER_RADIUS,
    STYLE_INPUT_PADDING, VOLUME_LABEL_FONT_SIZE, VOLUME_POPUP_RADIUS,
    VOLUME_SLIDER_GROOVE_WIDTH, VOLUME_SLIDER_HANDLE_SIZE,
)


def build_stylesheet() -> str:
    groove_radius = VOLUME_SLIDER_GROOVE_WIDTH // 2
    handle_overhang = (VOLUME_SLIDER_HANDLE_SIZE - VOLUME_SLIDER_GROOVE_WIDTH) // 2
    handle_radius = VOLUME_SLIDER_HANDLE_SIZE // 2
    return f"""
    QWidget {{
        background-color: {COLOR_BG};
        color: {COLOR_TEXT_PRIMARY};
        font-family: {FONT_FAMILY};
        font-size: {FONT_SIZE_NORMAL}pt;
    }}
    #{OBJECT_NAME_CANVAS_PANEL} {{
        background-color: {COLOR_CANVAS_BG};
    }}
    #{OBJECT_NAME_CHAT_PANEL} {{
        background-color: {COLOR_PANEL_BG};
        border-left: {STYLE_BORDER_WIDTH}px solid {COLOR_BORDER};
    }}
    QSplitter::handle {{
        background-color: {COLOR_BORDER};
    }}
    QSplitter::handle:hover {{
        background-color: {COLOR_ACCENT};
    }}
    QScrollArea#{OBJECT_NAME_CHAT_HISTORY} {{
        background-color: transparent;
        border: none;
    }}
    QScrollArea#{OBJECT_NAME_CHAT_HISTORY} > QWidget > QWidget {{
        background-color: transparent;
    }}
    QLabel#{OBJECT_NAME_USER_BUBBLE} {{
        background-color: {COLOR_BUBBLE_USER_BG};
        color: {COLOR_BUBBLE_TEXT};
        border-radius: {CHAT_BUBBLE_RADIUS}px;
        padding: {CHAT_BUBBLE_PADDING}px;
    }}
    QLabel#{OBJECT_NAME_AGENT_BUBBLE} {{
        background-color: {COLOR_BUBBLE_AGENT_BG};
        color: {COLOR_BUBBLE_TEXT};
        border-radius: {CHAT_BUBBLE_RADIUS}px;
        padding: {CHAT_BUBBLE_PADDING}px;
    }}
    QLineEdit {{
        background-color: {COLOR_INPUT_BG};
        border: {STYLE_BORDER_WIDTH}px solid {COLOR_BORDER};
        border-radius: {STYLE_INPUT_BORDER_RADIUS}px;
        padding: {STYLE_INPUT_PADDING}px;
    }}
    QLineEdit:focus {{
        border: {STYLE_BORDER_WIDTH}px solid {COLOR_ACCENT};
    }}
    QPushButton {{
        background-color: {COLOR_INPUT_BG};
        border: {STYLE_BORDER_WIDTH}px solid {COLOR_BORDER};
        border-radius: {STYLE_BUTTON_BORDER_RADIUS}px;
        padding: {STYLE_BUTTON_PADDING_V}px {STYLE_BUTTON_PADDING_H}px;
    }}
    QPushButton:hover {{
        border: {STYLE_BORDER_WIDTH}px solid {COLOR_ACCENT};
    }}
    QListWidget {{
        background-color: transparent;
        border: none;
    }}
    QPushButton#{OBJECT_NAME_MIC_TOGGLE_BUTTON}:checked {{
        border: {STYLE_BORDER_WIDTH}px solid {COLOR_MIC_ACTIVE};
        color: {COLOR_MIC_ACTIVE};
    }}
    QPushButton#{OBJECT_NAME_SEND_BUTTON}[busy="true"] {{
        background-color: {COLOR_STOP_ACTIVE};
        border: {STYLE_BORDER_WIDTH}px solid {COLOR_STOP_ACTIVE};
        color: #ffffff;
    }}
    QPushButton#{OBJECT_NAME_SEND_BUTTON}[busy="true"]:hover {{
        border: {STYLE_BORDER_WIDTH}px solid #ff8080;
    }}
    QScrollArea#{OBJECT_NAME_CHAT_HISTORY} QScrollBar:vertical {{
        background: {COLOR_SCROLLBAR_TRACK};
        width: {SCROLLBAR_WIDTH}px;
        margin: 0px;
        border: none;
    }}
    QScrollArea#{OBJECT_NAME_CHAT_HISTORY} QScrollBar::handle:vertical {{
        background: {COLOR_SCROLLBAR_HANDLE};
        min-height: {SCROLLBAR_HANDLE_MIN_HEIGHT}px;
        border-radius: {SCROLLBAR_HANDLE_RADIUS}px;
    }}
    QScrollArea#{OBJECT_NAME_CHAT_HISTORY} QScrollBar::handle:vertical:hover {{
        background: {COLOR_SCROLLBAR_HANDLE_HOVER};
    }}
    QScrollArea#{OBJECT_NAME_CHAT_HISTORY} QScrollBar::add-line:vertical,
    QScrollArea#{OBJECT_NAME_CHAT_HISTORY} QScrollBar::sub-line:vertical {{
        height: 0px;
        width: 0px;
        background: none;
        border: none;
    }}
    QScrollArea#{OBJECT_NAME_CHAT_HISTORY} QScrollBar::add-page:vertical,
    QScrollArea#{OBJECT_NAME_CHAT_HISTORY} QScrollBar::sub-page:vertical {{
        background: none;
    }}
    QPushButton#{OBJECT_NAME_MUTE_BUTTON} {{
        background-color: {COLOR_INPUT_BG};
        border: {STYLE_BORDER_WIDTH}px solid {COLOR_BORDER};
        border-radius: {MUTE_BUTTON_RADIUS}px;
        padding: 0px;
    }}
    QPushButton#{OBJECT_NAME_MUTE_BUTTON}:hover {{
        border: {STYLE_BORDER_WIDTH}px solid {COLOR_ACCENT};
    }}
    QPushButton#{OBJECT_NAME_MUTE_BUTTON}:checked {{
        background-color: {COLOR_INPUT_BG};
        border: {STYLE_BORDER_WIDTH}px solid {COLOR_MIC_ACTIVE};
    }}
    QFrame#{OBJECT_NAME_VOLUME_POPUP} {{
        background-color: {COLOR_INPUT_BG};
        border: {STYLE_BORDER_WIDTH}px solid {COLOR_BORDER};
        border-radius: {VOLUME_POPUP_RADIUS}px;
    }}
    QFrame#{OBJECT_NAME_VOLUME_POPUP} QLabel {{
        background-color: transparent;
        color: {COLOR_TEXT_SECONDARY};
        font-size: {VOLUME_LABEL_FONT_SIZE}pt;
    }}
    QSlider#{OBJECT_NAME_VOLUME_SLIDER} {{
        background-color: transparent;
    }}
    QSlider#{OBJECT_NAME_VOLUME_SLIDER}::groove:vertical {{
        background: {COLOR_BORDER};
        width: {VOLUME_SLIDER_GROOVE_WIDTH}px;
        border-radius: {groove_radius}px;
    }}
    QSlider#{OBJECT_NAME_VOLUME_SLIDER}::sub-page:vertical {{
        background: {COLOR_BORDER};
        border-radius: {groove_radius}px;
    }}
    QSlider#{OBJECT_NAME_VOLUME_SLIDER}::add-page:vertical {{
        background: {COLOR_ACCENT};
        border-radius: {groove_radius}px;
    }}
    QSlider#{OBJECT_NAME_VOLUME_SLIDER}::handle:vertical {{
        background: {COLOR_TEXT_PRIMARY};
        height: {VOLUME_SLIDER_HANDLE_SIZE}px;
        margin: 0px -{handle_overhang}px;
        border-radius: {handle_radius}px;
    }}
    QSlider#{OBJECT_NAME_VOLUME_SLIDER}::handle:vertical:hover {{
        background: {COLOR_ACCENT};
    }}
    """