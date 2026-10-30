import re


def normalize_phone(raw: str) -> str | None:
    """Digits only (keeping a leading +); None if it isn't a plausible phone number."""
    digits = re.sub(r'\D', '', raw)
    if not 7 <= len(digits) <= 15:
        return None
    return ('+' if raw.strip().startswith('+') else '') + digits
