from pathlib import Path

import streamlit as st

from ...parseData import parseTXT


def show():
    st.title("📁 Instance")
    st.write("Lade und zeige Instanzdaten an.")

    # File upload or selection
    uploaded_file = st.file_uploader("Wähle eine Instance-Datei", type=["txt"])

    if uploaded_file is not None:
        # Save uploaded file temporarily and parse
        st.success(f"Datei geladen: {uploaded_file.name}")
        # Add parsing and display logic here
    else:
        # Show default instance
        st.info("Zeige Standard-Instanz: Instance1.txt")
        test_file = (
            Path(__file__).resolve().parent.parent.parent.parent
            / "data"
            / "Instance1.txt"
        )
        if test_file.exists():
            inst = parseTXT.parse_txt(test_file)
            st.write("Instance geladen")
            # Display instance details
            st.json({"info": "Instance Details hier anzeigen"})
