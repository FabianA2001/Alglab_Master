import streamlit as st

from ... import shift_vars, solver


def show():
    st.title("⚙️ Solver")
    st.write("Konfiguriere und starte den Solver.")

    if "solution" in st.session_state and st.session_state["solution"] is not None:
        st.warning(
            "Der Solver hat bereits eine Lösung gefunden. Bitte starte die Anwendung neu, um den Solver erneut zu verwenden."
        )
        return

    # Solver configuration
    st.subheader("Solver Einstellungen")

    col1, col2 = st.columns(2)

    with col1:
        st.write("Parameter hier anzeigen/konfigurieren")

    with col2:
        st.write("Weitere Optionen")

    if "instance" in st.session_state:
        instance = st.session_state["instance"]
        # Run solver button
        if st.button("Solver starten", type="primary"):
            st.session_state["solver_started"] = True
            with st.spinner("Löse Problem..."):
                sol = solver.Solver(instance, shift_vars.Shift_vars(instance))
                solution = sol.solve(log_search_progress=False)
                # Store solution in session state
                st.session_state["solution"] = solution
                st.success("Lösung gefunden!")
                st.write("Gehe zur Solution-Seite um das Ergebnis zu sehen.")

    else:
        st.warning(
            "Keine Instanz geladen. Bitte zuerst zur Instance-Seite gehen und eine Instanz laden."
        )
