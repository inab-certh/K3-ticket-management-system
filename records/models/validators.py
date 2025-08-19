# records/validators.py
import re
from datetime import datetime
from django.core.exceptions import ValidationError

_AFΜ_RE = re.compile(r"^\d{9}$")
_AMKA_RE = re.compile(r"^\d{11}$")
# Allow either Greek (Α-Ω) or Latin (A-Z) letters, optionally a space/dash between letters and digits.
_ID_RE = re.compile(r"^[A-ZΑ-Ω]{2}[- ]?\d{6}$", re.IGNORECASE)

def _is_blank(value):
    return value is None or (isinstance(value, str) and value.strip() == "")

def validate_vat(value: str):
    """
    Greek VAT (ΑΦΜ) – 9 digits with checksum:
    checksum = sum(d_i * 2^(9-i) for i=1..8) % 11; if 10 => 0; must equal d9
    """
    if _is_blank(value):
        return  # let blank/null be handled by model null/blank
    v = value.strip()
    if not _AFΜ_RE.match(v):
        raise ValidationError("Ο ΑΦΜ πρέπει να είναι 9 ψηφία.")

    digits = list(map(int, v))
    s = sum(digits[i] * (2 ** (8 - i)) for i in range(8))
    check = s % 11
    if check == 10:
        check = 0
    if check != digits[8]:
        raise ValidationError("Μη έγκυρος ΑΦΜ (λάθος ψηφίο ελέγχου).")

def validate_amka(value: str):
    """
    AMKA – 11 digits. First 6 are DDMMYY; we sanity-check the date.
    """
    if _is_blank(value):
        return
    v = value.strip()
    if not _AMKA_RE.match(v):
        raise ValidationError("Ο ΑΜΚΑ πρέπει να είναι 11 ψηφία.")
    # basic date sanity (DDMMYY). AMKA doesn't encode century reliably; we just verify DD/MM/YY.
    dd, mm, yy = int(v[0:2]), int(v[2:4]), int(v[4:6])
    try:
        # pick a reference century (2000–2099 if yy < 25 else 1900–1999) just for validation
        year = 2000 + yy if yy < 25 else 1900 + yy
        datetime(year, mm, dd)
    except ValueError:
        raise ValidationError("Μη έγκυρη ημερομηνία γέννησης στα πρώτα 6 ψηφία του ΑΜΚΑ.")

def validate_id_card(value: str):
    """
    Greek ID: two letters + 6 digits (accept Greek or Latin letters, with optional '-' or space).
    """
    if _is_blank(value):
        return
    v = value.strip().upper().replace(" ", "").replace("-", "")
    if not re.match(r"^[A-ZΑ-Ω]{2}\d{6}$", v):
        raise ValidationError("Η ταυτότητα πρέπει να έχει μορφή π.χ. ΑΒ123456 (ή AB123456).")
