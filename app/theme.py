from app.config import (
    CHAT_BUBBLE_PADDING,
    CHAT_BUBBLE_RADIUS,
    COLOR_ACCENT,
    COLOR_BG,
    COLOR_BORDER,
    COLOR_BUBBLE_AGENT_BG,
    COLOR_BUBBLE_TEXT,
    COLOR_BUBBLE_USER_BG,
    COLOR_CANVAS_BG,
    COLOR_INPUT_BG,
    COLOR_MIC_ACTIVE,
    COLOR_PANEL_BG,
    COLOR_TEXT_PRIMARY,
    FONT_FAMILY,
    FONT_SIZE_NORMAL,
    OBJECT_NAME_AGENT_BUBBLE,
    OBJECT_NAME_CANVAS_PANEL,
    OBJECT_NAME_CHAT_HISTORY,
    OBJECT_NAME_CHAT_PANEL,
    OBJECT_NAME_MIC_TOGGLE_BUTTON,
    OBJECT_NAME_USER_BUBBLE,
    STYLE_BORDER_WIDTH,
    STYLE_BUTTON_BORDER_RADIUS,
    STYLE_BUTTON_PADDING_H,
    STYLE_BUTTON_PADDING_V,
    STYLE_INPUT_BORDER_RADIUS,
    STYLE_INPUT_PADDING,
    OBJECT_NAME_SEND_BUTTON,
    COLOR_STOP_ACTIVE,
)


def build_stylesheet() -> str:
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
    """