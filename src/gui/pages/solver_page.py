import logging
import time
from concurrent.futures import ThreadPoolExecutor

import streamlit as st

from ... import shift_vars, solution, solver
from ...LNS import lns, minimal_change_lns
from .session_state_names import Session_state_Names as SSN


def solve_warm_start(**kwargs) -> solution.Solution:
    """Führt den Solver in einem separaten Thread aus"""
    instance = kwargs["instance"]
    disabled_constraints = kwargs["disabled_constraints"]

    # TODO warm start implement
    old_solution = kwargs["old_solution"]
    sol = solver.Solver(
        instance,
        shift_vars.Shift_vars(instance),
        disabled_constraints=disabled_constraints,
    )
    sol = sol.warm_start(
        old_solution,
        max_time_in_seconds=kwargs["timeout_seconds"],
    )
    if sol.solve_status == 4 or sol.solve_status == 2:
        sol.to_json_file(instance.name)
    return sol


def solve(**kwargs) -> solution.Solution:
    """Führt den Solver in einem separaten Thread aus"""
    instance = kwargs["instance"]
    disabled_constraints = kwargs["disabled_constraints"]
    sol = solver.Solver(
        instance,
        shift_vars.Shift_vars(instance),
        disabled_constraints=disabled_constraints,
    )
    sol = sol.solve_with_early_stop(
        log_search_progress=False,
        max_time_in_seconds=kwargs["timeout_seconds"],
    )
    if sol.solve_status == 4 or sol.solve_status == 2:
        sol.to_json_file(instance.name)
    return sol


def solve_with_lns(**kwargs) -> solution.Solution:
    """Führt den Solver in einem separaten Thread aus"""
    inst_sol = kwargs["instance_solution"]
    disabled_constraints = kwargs["disabled_constraints"]
    if disabled_constraints != []:
        st.error("⚠️ LNS unterstützt derzeit keine Deaktivierung von Constraints.")
        assert False
    lns_solver = lns.LNS(
        inst_sol,
        timeout_seconds=kwargs["timeout_seconds"],
        log_level=logging.ERROR,
    )
    sol = lns_solver.solve()
    if sol.solve_status == 4 or sol.solve_status == 2:
        sol.to_json_file(sol.instance.name)
    return sol


def solve_with_lns_minimal_changes(**kwargs) -> solution.Solution:
    """Führt den Solver in einem separaten Thread aus"""
    sol = kwargs["solution"]
    old_solution = kwargs["solution"]
    inst = kwargs["instance"]
    disabled_constraints = kwargs["disabled_constraints"]
    if disabled_constraints != []:
        st.error("⚠️ LNS unterstützt derzeit keine Deaktivierung von Constraints.")
        assert False
    old_solution.instance = inst
    sol = minimal_change_lns.solve_changes(
        old_solution=old_solution,
        days_with_change=kwargs["days_with_change"],
        max_solve_time=kwargs["timeout_seconds"],
        log_search_progress=False,
    )
    if sol.solve_status == 4 or sol.solve_status == 2:
        sol.to_json_file(sol.instance.name)
    else:
        print("keine Lösung gefunden bei minimal changes LNS")
    return sol


def run_solver_in_thread(solve_funktion=solve, **kwargs):
    # Speichere den aktuellen Timeout-Wert
    st.session_state[SSN.solver_running.name] = True
    st.session_state[SSN.allow_resolve.name] = False
    st.session_state[SSN.solver_start_time.name] = time.time()

    # Start solver in a subprocess
    executor = ThreadPoolExecutor()
    future = executor.submit(solve_funktion, **kwargs)

    st.session_state[SSN.solver_executor.name] = executor
    st.session_state[SSN.solver_future.name] = future
    st.rerun()


def show():
    st.title("⚙️ Solver")
    st.write("Konfiguriere und starte den Solver.")

    # if (
    #     st.session_state[SSN.solutions.name] != []
    #     and not st.session_state[SSN.allow_resolve.name]
    #     and not st.session_state[SSN.solver_running.name]
    # ):
    #     st.success("✅ Der Solver hat eine Lösung gefunden!")

    #     # Zeige die aktiven Constraints der aktuellen Lösung
    #     sol = st.session_state[SSN.solutions.name][-1]
    #     show_active_constraints(sol)

    #     st.info(
    #         "💡 Gehe zur Solution-Seite um das Ergebnis zu sehen oder starte die Anwendung neu, um den Solver erneut zu verwenden."
    #     )
    #     return

    # Solver configuration
    st.subheader("Solver Einstellungen")

    # Timeout Input
    if SSN.solver_timeout.name not in st.session_state:
        st.session_state[SSN.solver_timeout.name] = 60.0

    timeout_seconds = st.number_input(
        "Solver Timeout (Sekunden)",
        min_value=1.0,
        max_value=3600.0,
        value=st.session_state[SSN.solver_timeout.name],
        step=1.0,
        help="Maximale Zeit in Sekunden, die der Solver laufen soll. Standard: 60 Sekunden (1 Minute)",
        key="timeout_input",
    )
    st.session_state[SSN.solver_timeout.name] = timeout_seconds

    if SSN.disabled_constraints.name not in st.session_state:
        st.session_state[SSN.disabled_constraints.name] = {}
    disabled_constraints_value: dict[solver.SolverConstraints, bool] = st.session_state[
        SSN.disabled_constraints.name
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
            key=f"toggle_{mode.name}",
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
    toggle_constraint(solver.SolverConstraints.assign_employee_day_shift)
    toggle_constraint(solver.SolverConstraints.ban_employee_day_shift)

    st.session_state[SSN.disabled_constraints.name] = disabled_constraints_value
    disabled_constraints: list[solver.SolverConstraints] = []
    for key, value in disabled_constraints_value.items():
        if not value:
            disabled_constraints.append(key)

    if SSN.instance.name in st.session_state:
        # Initialize solver state
        if SSN.solver_running.name not in st.session_state:
            st.session_state[SSN.solver_running.name] = False
        if SSN.solver_executor.name not in st.session_state:
            st.session_state[SSN.solver_executor.name] = None
        if SSN.solver_future.name not in st.session_state:
            st.session_state[SSN.solver_future.name] = None
        if SSN.solver_start_time.name not in st.session_state:
            st.session_state[SSN.solver_start_time.name] = None

        if (
            len(st.session_state[SSN.solutions.name]) == 0
            or st.session_state[SSN.allow_resolve.name]
        ):
            if st.button(
                "Solver starten",
                type="primary",
                disabled=st.session_state[SSN.solver_running.name],
                key="start_solver_button",
            ):
                run_solver_in_thread(
                    solve_funktion=solve,
                    instance=st.session_state[SSN.instance.name],
                    disabled_constraints=disabled_constraints,
                    timeout_seconds=st.session_state[SSN.solver_timeout.name],
                )

        if (
            len(st.session_state[SSN.solutions.name]) > 0
            and st.session_state[SSN.allow_resolve.name]
        ):
            if st.button(
                "Warm start",
                type="primary",
                disabled=st.session_state[SSN.solver_running.name],
                key="warm_start_solver_button",
            ):
                run_solver_in_thread(
                    solve_funktion=solve_warm_start,
                    instance=st.session_state[SSN.instance.name],
                    disabled_constraints=disabled_constraints,
                    old_solution=st.session_state[SSN.solutions.name][-1],
                    timeout_seconds=st.session_state[SSN.solver_timeout.name],
                )

        # TODO: change LNS Parameter
        if (
            len(st.session_state[SSN.solutions.name]) > 0
            and st.session_state[SSN.allow_resolve.name]
        ) or len(st.session_state[SSN.solutions.name]) == 0:
            if st.button(
                "Large neighborhood search",
                type="primary",
                disabled=st.session_state[SSN.solver_running.name],
                key="lns_start_solver_button",
            ):
                inst_sol = (
                    st.session_state[SSN.instance.name]
                    if len(st.session_state[SSN.solutions.name]) == 0
                    else st.session_state[SSN.solutions.name][-1]
                )
                run_solver_in_thread(
                    solve_funktion=solve_with_lns,
                    instance_solution=inst_sol,
                    disabled_constraints=disabled_constraints,
                    timeout_seconds=st.session_state[SSN.solver_timeout.name],
                )

        if (
            len(st.session_state[SSN.solutions.name]) > 0
            and st.session_state[SSN.allow_resolve.name]
        ):
            if st.button(
                "Minimal Changes with Large neighborhood search",
                type="primary",
                disabled=st.session_state[SSN.solver_running.name],
                key="lns_changs_start_solver_button",
            ):
                print(f"changs_days: {st.session_state[SSN.changes_days.name]}")
                run_solver_in_thread(
                    solve_funktion=solve_with_lns_minimal_changes,
                    instance=st.session_state[SSN.instance.name],
                    solution=st.session_state[SSN.solutions.name][-1],
                    disabled_constraints=disabled_constraints,
                    timeout_seconds=st.session_state[SSN.solver_timeout.name],
                    days_with_change=st.session_state[SSN.changes_days.name],
                )

        # Check if solver is running
        if st.session_state[SSN.solver_running.name]:
            future = st.session_state[SSN.solver_future.name]

            if future.done():
                # Solver finished
                try:
                    solution = future.result()
                    st.session_state[SSN.solver_future.name] = None
                    elapsed_time = (
                        time.time() - st.session_state[SSN.solver_start_time.name]
                    )
                    st.session_state[SSN.solver_running.name] = False
                    st.session_state[SSN.solver_executor.name].shutdown(wait=False)
                    if solution.solve_status == 2:
                        st.session_state[SSN.solutions.name].append(solution)
                        st.success(
                            f"A solution has been found! (Runtime: {elapsed_time:.2f} seconds)"
                        )
                        st.write("Go to solution page to see the solution.")
                    elif solution.solve_status == 0:
                        st.error(
                            f"The Time limit has been reached without finding a solution (Runtime: {elapsed_time:.2f} seconds)"
                        )
                    elif solution.solve_status == 1:
                        st.error(
                            f"Model isn't valid (Runtime: {elapsed_time:.2f} seconds)"
                        )
                    elif solution.solve_status == 3:
                        st.error(
                            f"Model is infeasible (Runtime: {elapsed_time:.2f} seconds)"
                        )
                    elif solution.solve_status == 4:
                        st.session_state[SSN.solutions.name].append(solution)
                        st.success(
                            f"An optimal solution has been found! (Runtime: {elapsed_time:.2f} seconds)"
                        )
                        st.write("Go to solution page to see the solution.")

                except Exception as e:
                    st.error(f"Fehler beim Lösen: {str(e)}")
                    st.session_state[SSN.solver_running.name] = False
                    st.session_state[SSN.solver_executor.name].shutdown(wait=False)
            else:
                # Solver still running
                elapsed_time = (
                    time.time() - st.session_state[SSN.solver_start_time.name]
                )
                st.info(
                    f"Solver läuft im Hintergrund... (Laufzeit: {elapsed_time:.1f} Sekunden)"
                )
                time.sleep(0.5)
                st.rerun()

    else:
        st.warning(
            "Keine Instanz geladen. Bitte zuerst zur Instance-Seite gehen und eine Instanz laden."
        )
