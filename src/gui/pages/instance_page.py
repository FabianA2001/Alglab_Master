from pathlib import Path

import streamlit as st

from ...parseData import parseTXT

DATA_DIR = (
    Path(__file__).resolve().parent.parent.parent.parent / "data" / "instance_raw"
)
DEFAULT_PATH = DATA_DIR / "Instance1.txt"


def get_instance_files():
    """Holt alle .txt Dateien aus dem data Ordner"""
    if DATA_DIR.exists():
        txt_files = list(DATA_DIR.glob("*.txt"))
        return sorted([f.name for f in txt_files])
    return []


def show():
    st.title("📁 Instance")
    st.write("Lade und zeige Instanzdaten an.")

    if "solution" in st.session_state and st.session_state["solution"] is not None:
        st.warning(
            "Der Solver hat bereits eine Lösung gefunden. Bitte starte die Anwendung neu, um den Solver erneut zu verwenden."
        )
        return

    if st.session_state["solver_running"]:
        st.warning(
            "Die Instanz kann nicht geändert werden, da der Solver bereits gestartet wurde."
        )
        return

    # Dropdown für Dateien aus dem data Ordner
    instance_files = get_instance_files()

    if instance_files:
        # Standardauswahl auf Instance1.txt setzen, falls vorhanden
        default_index = 0
        if "Instance1.txt" in instance_files:
            default_index = instance_files.index("Instance1.txt")

        selected_file = st.selectbox(
            "Wähle eine Instance aus dem data Ordner",
            instance_files,
            index=default_index,
        )

        path = DATA_DIR / selected_file
        if path.exists():
            inst = parseTXT.parse_txt(path)
            st.session_state["instance"] = inst
            st.success(f"Datei geladen: {selected_file}")
        else:
            st.error("Datei nicht gefunden.")
    else:
        st.error("Keine Instanz-Dateien im data Ordner gefunden.")

    st.divider()
