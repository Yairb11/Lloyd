import re

# Move to config.py 
# Maybe Ill add something more to here
def clean_text_for_speech(text: str) -> str:
    text = re.sub(r"[\*#_`~]", "", text)
    text = re.sub(
        r"[\U00010000-\U0010ffff]", "", text
    )

    fractions = {
        "1/2": "half",
        "1/4": "quarter",
        "3/4": "three quarters",
        "1/3": "one third",
        "2/3": "two thirds",
    }
    for frac, replacement in fractions.items():
        text = re.sub(rf"\b{re.escape(frac)}\b", replacement, text)

    text = re.sub(r"(\d+(?:\.\d+)?)\s*ml\b", r"\1 milliliters", text, flags=re.IGNORECASE)
    text = re.sub(r"(\d+(?:\.\d+)?)\s*cl\b", r"\1 centiliters", text, flags=re.IGNORECASE)
    text = re.sub(r"(\d+(?:\.\d+)?)\s*oz\b", r"\1 ounces", text, flags=re.IGNORECASE)

    text = re.sub(r"(\d+)\s*-\s*(\d+)", r"\1 to \2", text)
    text = re.sub(r"(\d+)\s*°\s*C", r"\1 degrees Celsius", text)

    return text.strip()