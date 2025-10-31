import pandas as pd
import streamlit as st

# Beispiel-Daten
shift_types = ["Frühschicht", "Spätschicht", "Nachtschicht"]
days = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag"]

# Beispielhafte Mitarbeiterbelegung
data = {
    day: [
        ["Anna", "Ben"],  # Früh
        ["Clara"],  # Spät
        ["Daniel", "Elias"],  # Nacht
    ]
    for day in days
}

df = pd.DataFrame(data, index=shift_types)


def show():
    st.title("✅ Solution")
    st.write("Zeige die berechnete Lösung an.")

    # # Check if solution exists in session state
    # if "solution" not in st.session_state:
    #     st.warning("Keine Lösung verfügbar. Bitte zuerst den Solver ausführen.")
    #     st.info("Gehe zur Solver-Seite um eine Lösung zu berechnen.")
    #     return

    # solution = st.session_state["solution"]

    # st.subheader("Lösung Details")
    edited_df = st.data_editor(
        df,
        key="shiftplan",
    )
