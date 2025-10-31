from pathlib import Path

import streamlit as st

from ... import shift_vars, solver
from ...parseData import parseTXT


def show():
    st.title("⚙️ Solver")
    st.write("Konfiguriere und starte den Solver.")

    # Solver configuration
    st.subheader("Solver Einstellungen")

    col1, col2 = st.columns(2)

    with col1:
        st.write("Parameter hier anzeigen/konfigurieren")

    with col2:
        st.write("Weitere Optionen")

    # Run solver button
    if st.button("Solver starten", type="primary"):
        with st.spinner("Löse Problem..."):
            test_file = (
                Path(__file__).resolve().parent.parent.parent.parent
                / "data"
                / "Instance1.txt"
            )
            inst = parseTXT.parse_txt(test_file)
            sol = solver.Solver(inst, shift_vars.Shift_vars(inst))
            solution = sol.solve()

            # Store solution in session state
            st.session_state["solution"] = solution
            st.success("Lösung gefunden!")
            st.write("Gehe zur Solution-Seite um das Ergebnis zu sehen.")
