from theme import THEME

def get_stylesheet():
    return f"""
    QMainWindow {{
        background-color: {THEME['background']};
        font-family: {THEME['font_family']};
        font-size: {THEME['font_size']};
    }}
    QPushButton {{
        background-color: {THEME['primary']};
        color: white;
        border: none;
        border-radius: 6px;
        padding: 8px 16px;
    }}
    QPushButton:hover {{
        background-color: {THEME['primary_dark']};
    }}
    QLineEdit {{
        background-color: white;
        border: 2px solid {THEME['neutral']};
        border-radius: 6px;
        padding: 8px;
    }}
    QLineEdit:focus {{
        border-color: {THEME['primary']};
    }}
    QTextBrowser {{
        background-color: white;
        border: 1px solid {THEME['neutral']};
        border-radius: 6px;
        padding: 10px;
        font-size: 15px;
    }}
    QTextEdit {{
        background-color: {THEME['highlight']};
        border: 1px solid {THEME['neutral']};
        border-radius: 6px;
        padding: 10px;
        color: {THEME['highlight_text']};
        font-style: italic;
    }}
    """
