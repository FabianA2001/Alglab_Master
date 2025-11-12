import time
from concurrent.futures import ThreadPoolExecutor

import streamlit as st

from ... import shift_vars, solution, solver
from ...inputTypes import instace
from .session_state_names import Session_state_Names as SSN
from .show_constraints import show_active_constraints


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

    if (
        SSN.solution.name in st.session_state
        and st.session_state[SSN.solution.name] is not None
        and SSN.reset_solver.name not in st.session_state
    ):
        st.success("✅ Der Solver hat eine Lösung gefunden!")

        # Zeige die aktiven Constraints der aktuellen Lösung
        sol = st.session_state[SSN.solution.name]
        show_active_constraints(sol)

        st.info(
            "💡 Gehe zur Solution-Seite um das Ergebnis zu sehen oder starte die Anwendung neu, um den Solver erneut zu verwenden."
        )
        return

    # Solver configuration
    st.subheader("Solver Einstellungen")

    if SSN.disabled_constraints_value.name not in st.session_state:
        st.session_state[SSN.disabled_constraints_value.name] = {}
    disabled_constraints_value: dict[solver.SolverConstraints, bool] = st.session_state[
        SSN.disabled_constraints_value.name
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

    if SSN.instance.name in st.session_state:
        instance = st.session_state[SSN.instance.name]

        # Initialize solver state
        if SSN.solver_running.name not in st.session_state:
            st.session_state[SSN.solver_running.name] = False
        if SSN.solver_executor.name not in st.session_state:
            st.session_state[SSN.solver_executor.name] = None
        if SSN.solver_future.name not in st.session_state:
            st.session_state[SSN.solver_future.name] = None
        if SSN.solver_start_time.name not in st.session_state:
            st.session_state[SSN.solver_start_time.name] = None

        # Run solver button
        if st.button(
            "Solver starten",
            type="primary",
            disabled=st.session_state[SSN.solver_running.name],
        ):
            st.session_state[SSN.solver_running.name] = True
            st.session_state[SSN.solver_start_time.name] = time.time()

            # Start solver in a subprocess
            executor = ThreadPoolExecutor()
            future = executor.submit(solve_in_thread, instance, disabled_constraints)

            st.session_state[SSN.solver_executor.name] = executor
            st.session_state[SSN.solver_future.name] = future
            st.rerun()

        # Check if solver is running
        if st.session_state[SSN.solver_running.name]:
            future = st.session_state[SSN.solver_future.name]

            if future.done():
                # Solver finished
                try:
                    solution = future.result()
                    st.session_state[SSN.solution.name] = solution
                    elapsed_time = time.time() - st.session_state[SSN.solver_start_time.name]
                    st.session_state[SSN.solver_running.name] = False
                    st.session_state[SSN.solver_executor.name].shutdown(wait=False)
                    st.success(
                        f"Lösung gefunden! (Laufzeit: {elapsed_time:.2f} Sekunden)"
                    )
                    st.write("Gehe zur Solution-Seite um das Ergebnis zu sehen.")
                except Exception as e:
                    st.error(f"Fehler beim Lösen: {str(e)}")
                    st.session_state[SSN.solver_running.name] = False
                    st.session_state[SSN.solver_executor.name].shutdown(wait=False)
            else:
                # Solver still running
                elapsed_time = time.time() - st.session_state[SSN.solver_start_time.name]
                st.info(
                    f"Solver läuft im Hintergrund... (Laufzeit: {elapsed_time:.1f} Sekunden)"
                )
                time.sleep(0.5)
                st.rerun()

    else:
        st.warning(
            "Keine Instanz geladen. Bitte zuerst zur Instance-Seite gehen und eine Instanz laden."
        )
