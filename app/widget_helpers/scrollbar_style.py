from app.config import (
    COLOR_SCROLLBAR_HANDLE, COLOR_SCROLLBAR_HANDLE_HOVER, COLOR_SCROLLBAR_TRACK,
    SCROLLBAR_HANDLE_MIN_HEIGHT, SCROLLBAR_HANDLE_RADIUS, SCROLLBAR_WIDTH,
)


def build_scrollbar_stylesheet() -> str:
    return f"""
    QScrollBar:vertical {{
        background: {COLOR_SCROLLBAR_TRACK};
        width: {SCROLLBAR_WIDTH}px;
        margin: 0px;
        border: none;
    }}
    QScrollBar:horizontal {{
        background: {COLOR_SCROLLBAR_TRACK};
        height: {SCROLLBAR_WIDTH}px;
        margin: 0px;
        border: none;
    }}
    QScrollBar::handle:vertical {{
        background: {COLOR_SCROLLBAR_HANDLE};
        min-height: {SCROLLBAR_HANDLE_MIN_HEIGHT}px;
        border-radius: {SCROLLBAR_HANDLE_RADIUS}px;
    }}
    QScrollBar::handle:horizontal {{
        background: {COLOR_SCROLLBAR_HANDLE};
        min-width: {SCROLLBAR_HANDLE_MIN_HEIGHT}px;
        border-radius: {SCROLLBAR_HANDLE_RADIUS}px;
    }}
    QScrollBar::handle:vertical:hover,
    QScrollBar::handle:horizontal:hover {{
        background: {COLOR_SCROLLBAR_HANDLE_HOVER};
    }}
    QScrollBar::add-line:vertical,
    QScrollBar::sub-line:vertical,
    QScrollBar::add-line:horizontal,
    QScrollBar::sub-line:horizontal {{
        height: 0px;
        width: 0px;
        background: none;
        border: none;
    }}
    QScrollBar::add-page:vertical,
    QScrollBar::sub-page:vertical,
    QScrollBar::add-page:horizontal,
    QScrollBar::sub-page:horizontal {{
        background: none;
    }}
    """