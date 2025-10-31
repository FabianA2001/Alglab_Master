import pandas as pd
import streamlit as st

from ... import solution


def soluation_to_dataframe(solution: solution.Solution) -> pd.DataFrame:
    # Diese Funktion sollte die Lösung in ein DataFrame umwandeln
    days = [day for day in range(solution.instance.number_of_days)]
    shift_types = [
        shift_type.name for shift_type in solution.instance.shift_types.values()
    ]
    blank_data = {day: [[] for _ in shift_types] for day in days}
    df = pd.DataFrame(blank_data, index=shift_types)
    return df


def show():
    st.title("✅ Solution")
    st.write("Zeige die berechnete Lösung an.")

    # Check if solution exists in session state
    if "solution" not in st.session_state:
        st.warning("Keine Lösung verfügbar. Bitte zuerst den Solver ausführen.")
        st.info("Gehe zur Solver-Seite um eine Lösung zu berechnen.")
        return

    solution = st.session_state["solution"]

    st.data_editor(
        soluation_to_dataframe(solution),
        key="shiftplan",
    )
