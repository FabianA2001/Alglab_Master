"""Helper-Funktionen für die Solution-Page."""

from pathlib import Path

from ....help_functions import natural_sort_key

# Constants
DATA_DIR = (
    Path(__file__).resolve().parent.parent.parent.parent.parent / "data" / "solutions"
)


def load_available_solutions() -> list[str]:
    """Lädt alle verfügbaren Solution-Dateien aus dem DATA_DIR.

    Returns:
        list[str]: Sortierte Liste der Solution-Namen (ohne .json Endung)
    """
    if not DATA_DIR.exists():
        return []

    json_files = sorted([f.stem for f in DATA_DIR.glob("*.json")], key=natural_sort_key)
    return json_files
