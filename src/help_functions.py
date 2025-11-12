import hashlib


def hash_string(s: str) -> int:
    """Erstellt einen konsistenten Hash-Wert für einen gegebenen String."""
    return int(hashlib.md5(s.encode()).hexdigest(), 16)
