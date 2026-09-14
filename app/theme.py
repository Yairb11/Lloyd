from app import config


def build_stylesheet() -> str:
    return f"""
    QWidget {{
        background-color: {config.COLOR_BG};
        color: {config.COLOR_TEXT_PRIMARY};
        font-family: {config.FONT_FAMILY};
        font-size: {config.FONT_SIZE_NORMAL}pt;
    }}
    #canvasPanel {{
        background-color: {config.COLOR_CANVAS_BG};
    }}
    #chatPanel {{
        background-color: {config.COLOR_PANEL_BG};
        border-left: 1px solid {config.COLOR_BORDER};
    }}
    QSplitter::handle {{
        background-color: {config.COLOR_BORDER};
    }}
    QSplitter::handle:hover {{
        background-color: {config.COLOR_ACCENT};
    }}
    QScrollArea#chatHistory {{
        background-color: transparent;
        border: none;
    }}
    QScrollArea#chatHistory > QWidget > QWidget {{
        background-color: transparent;
    }}
    QLabel#userBubble {{
        background-color: {config.COLOR_BUBBLE_USER_BG};
        color: {config.COLOR_BUBBLE_TEXT};
        border-radius: {config.CHAT_BUBBLE_RADIUS}px;
        padding: {config.CHAT_BUBBLE_PADDING}px;
    }}
    QLabel#agentBubble {{
        background-color: {config.COLOR_BUBBLE_AGENT_BG};
        color: {config.COLOR_BUBBLE_TEXT};
        border-radius: {config.CHAT_BUBBLE_RADIUS}px;
        padding: {config.CHAT_BUBBLE_PADDING}px;
    }}
    QLineEdit {{
        background-color: {config.COLOR_INPUT_BG};
        border: 1px solid {config.COLOR_BORDER};
        border-radius: 6px;
        padding: 8px;
    }}
    QLineEdit:focus {{
        border: 1px solid {config.COLOR_ACCENT};
    }}
    QPushButton {{
        background-color: {config.COLOR_INPUT_BG};
        border: 1px solid {config.COLOR_BORDER};
        border-radius: 6px;
        padding: 8px 14px;
    }}
    QPushButton:hover {{
        border: 1px solid {config.COLOR_ACCENT};
    }}
    QListWidget {{
        background-color: transparent;
        border: none;
    }}
    QPushButton#micToggleButton:checked {{
        border: 1px solid #ff5c5c;
        color: #ff5c5c;
    }}
    """