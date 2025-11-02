import time
from concurrent.futures import ThreadPoolExecutor

import streamlit as st

from ... import shift_vars, solution, solver
from ...inputTypes import instace


def solve_in_thread(
    instance: instace.Instance,
    disabled_constraints: list[solver.SolverConstraints] = [],
) -> solution.Solution:
    """Führt den Solver in einem separaten Thread aus"""
    sol = solver.Solver(instance, shift_vars.Shift_vars(instance))
    sol = sol.solve(
        log_search_progress=False, disabled_constraints=disabled_constraints
    )
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

    if "disabled_constraints_value" not in st.session_state:
        st.session_state["disabled_constraints_value"] = {}
    disabled_constraints_value: dict[solver.SolverConstraints, bool] = st.session_state[
        "disabled_constraints_value"
    ]

    def toggle_constraint(mode: solver.SolverConstraints):
        default = (
            disabled_constraints_value[mode]
            if mode in disabled_constraints_value
            else True
        )
        disabled_constraints_value[mode] = st.toggle(
            f"{mode.name.replace('_', ' ')}",
            value=default,
        )

    toggle_constraint(solver.SolverConstraints.cover_requirements)
    toggle_constraint(solver.SolverConstraints.days_off)
    toggle_constraint(solver.SolverConstraints.limited_shifts_per_type_validation)
    toggle_constraint(solver.SolverConstraints.max_Cons_Shifts)
    toggle_constraint(solver.SolverConstraints.max_weekend_days)
    toggle_constraint(solver.SolverConstraints.minimum_consecutive_days_off)
    toggle_constraint(solver.SolverConstraints.minimum_consecutive_shifts)
    toggle_constraint(solver.SolverConstraints.minMaxWorkTime)
    toggle_constraint(solver.SolverConstraints.shift_assignment_single_day_validation)
    toggle_constraint(solver.SolverConstraints.shift_rotation_constraint)

    disabled_constraints: list[solver.SolverConstraints] = []
    for key, value in disabled_constraints_value.items():
        if not value:
            disabled_constraints.append(key)

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
            future = executor.submit(solve_in_thread, instance, disabled_constraints)

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
