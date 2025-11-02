import time
from concurrent.futures import ThreadPoolExecutor

import streamlit as st

from ... import shift_vars, solution, solver
from ...inputTypes import instace


def solve_in_thread(instance: instace.Instance) -> solution.Solution:
    """Führt den Solver in einem separaten Thread aus"""
    sol = solver.Solver(instance, shift_vars.Shift_vars(instance))
    sol = sol.solve(log_search_progress=False)
    sol.to_json_file(instance.name)
    return sol


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

        # Initialize solver state
        if "solver_running" not in st.session_state:
            st.session_state["solver_running"] = False
        if "solver_executor" not in st.session_state:
            st.session_state["solver_executor"] = None
        if "solver_future" not in st.session_state:
            st.session_state["solver_future"] = None

        # Run solver button
        if st.button(
            "Solver starten",
            type="primary",
            disabled=st.session_state["solver_running"],
        ):
            st.session_state["solver_running"] = True

            # Start solver in a subprocess
            executor = ThreadPoolExecutor(max_workers=1)
            future = executor.submit(solve_in_thread, instance)

            st.session_state["solver_executor"] = executor
            st.session_state["solver_future"] = future
            st.rerun()

        # Check if solver is running
        if st.session_state["solver_running"]:
            future = st.session_state["solver_future"]

            if future.done():
                # Solver finished
                try:
                    solution = future.result()
                    st.session_state["solution"] = solution
                    st.session_state["solver_running"] = False
                    st.session_state["solver_executor"].shutdown(wait=False)
                    st.success("Lösung gefunden!")
                    st.write("Gehe zur Solution-Seite um das Ergebnis zu sehen.")
                except Exception as e:
                    st.error(f"Fehler beim Lösen: {str(e)}")
                    st.session_state["solver_running"] = False
                    st.session_state["solver_executor"].shutdown(wait=False)
            else:
                # Solver still running
                st.info("Solver läuft im Hintergrund...")
                time.sleep(0.5)
                st.rerun()

    else:
        st.warning(
            "Keine Instanz geladen. Bitte zuerst zur Instance-Seite gehen und eine Instanz laden."
        )
