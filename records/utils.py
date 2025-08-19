# records/utils.py
import unicodedata

def greek_upper_no_tone(text: str) -> str:
    """
    Convert Greek (or Latin) text to uppercase without tonos/diacritics.
    Strips leading/trailing whitespace and collapses multiple spaces.
    Returns the original value if None/empty.
    """
    if not text:
        return text  # Keep None or empty string as is
    
    # Normalize whitespace
    text = " ".join(str(text).split())
    # Uppercase
    text = text.upper()
    # Remove diacritics/tonos
    return ''.join(
        c for c in unicodedata.normalize('NFD', text)
        if unicodedata.category(c) != 'Mn'
    )
