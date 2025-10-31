from pathlib import Path

import streamlit as st

from ...parseData import parseTXT

DEFAULT_PATH = (
    Path(__file__).resolve().parent.parent.parent.parent / "data" / "Instance1.txt"
)


def show():
    st.title("📁 Instance")
    st.write("Lade und zeige Instanzdaten an.")

    if st.session_state["solver_started"]:
        st.warning(
            "Die Instanz kann nicht geändert werden, da der Solver bereits gestartet wurde."
        )
        return
    # File upload or selection
    uploaded_file = st.file_uploader("Wähle eine Instance-Datei", type=["txt"])
    path = DEFAULT_PATH

    if uploaded_file is not None:
        # Save uploaded file temporarily and parse
        st.success(f"Datei geladen: {uploaded_file.name}")
        path = Path(uploaded_file.name)
        if not path.exists():
            st.error("Datei nicht gefunden.")
        else:
            inst = parseTXT.parse_txt(path)
            st.session_state["instance"] = inst
            st.success("Instanz in Session gespeichert!")
    else:
        # Show default instance
        st.info("nutze Standard-Instanz: Instance1.txt")
