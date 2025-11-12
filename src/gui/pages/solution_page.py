from datetime import time
from pathlib import Path

import streamlit as st

from ... import solution
from ...help_functions import hash_string
from .component_solution import my_component
from .session_state_names import Session_state_Names as SSN
from .show_constraints import show_active_constraints, show_constraint_violations

SOLUTION_DIR = (
    Path(__file__).resolve().parent.parent.parent.parent / "data" / "solutions"
)


def add_minutes_to_time(start_time: time, minutes: int) -> time:
    """Addiert Minuten zu einer time und gibt die neue time zurück."""
    total_minutes = start_time.hour * 60 + start_time.minute + minutes
    hours = (total_minutes // 60) % 24
    mins = total_minutes % 60
    return time(hours, mins)


def solution_to_html_data(sol: solution.Solution) -> dict:
    """Konvertiert die Lösung in ein Format für die Custom HTML Komponente"""

    days = [day for day in range(sol.instance.number_of_days)]

    # Erstelle erweiterte Shift-Type-Informationen mit Start- und Endzeit
    shift_types_info = []
    for shift_type in sol.instance.shift_types.values():
        start_time = shift_type.start_time
        # Berechne Endzeit basierend auf Länge in Minuten
        end_time = add_minutes_to_time(start_time, shift_type.length)

        shift_types_info.append(
            {
                "name": shift_type.name,
                "start_time": start_time.strftime("%H:%M"),
                "end_time": end_time.strftime("%H:%M"),
                "display_name": f"{shift_type.name} ({start_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')})",
            }
        )

    data = []
    for shift_type_uid in sol.instance.shift_types:
        row = []
        for day in days:
            assigned_employees = []
            for emp_id in sol.instance.employees:
                if sol.is_employee_assigned(day, shift_type_uid, emp_id):
                    assigned_employees.append(sol.instance.employees[emp_id].name)

            # Hole die bevorzugte Anzahl an Mitarbeitern für diese Schicht
            shift = sol.instance.get_shift(day, shift_type_uid)
            preferred_count = shift.preffert_number_employees
            actual_count = len(assigned_employees)
            difference = actual_count - preferred_count

            row.append(
                {
                    "employees": assigned_employees,
                    "preferred": preferred_count,
                    "actual": actual_count,
                    "difference": difference,
                    "weight": sol.instance.shifts[day][
                        shift_type_uid
                    ].weight_below_preferred,
                }
            )
        data.append(row)

    return {
        "shift_types_info": shift_types_info,
        "num_days": sol.instance.number_of_days,
        "data": data,
    }


def render_shift_plan_component(sol: solution.Solution, read_only: bool = False):
    """Rendert die Custom HTML/JS Komponente für den Shift Plan"""
    import json

    # Konvertiere Lösung in JSON-Format
    shift_plan_data = solution_to_html_data(sol)

    response_cover_requirement = my_component.my_component(
        "shift_plan_component",
        render_option="shift_plan_solution",
        data=json.dumps(shift_plan_data),
    )
    # TODO Disable button when read_only is True
    if read_only:
        return
    st.markdown(f"The selected employee is: {response_cover_requirement}")
    if response_cover_requirement != {}:
        instance = sol.instance.model_copy(deep=True)
        for day, shift_type_dict in response_cover_requirement.items():
            for shift_type, value in shift_type_dict.items():
                # TODO what about weight_above_preferred?
                instance.shifts[int(day)][
                    hash_string(shift_type)
                ].weight_below_preferred = int(value)
        st.session_state[SSN.instance.name] = instance
        st.success("Instance updated with new cover requirements from component.")
        st.session_state[SSN.allow_resolve.name] = True


def show():
    st.title("✅ Solution")
    # Check if solution exists in session state
    if (
        SSN.solutions.name not in st.session_state
        or st.session_state[SSN.solutions.name] == []
    ):
        st.warning(
            "Keine Lösung verfügbar. Bitte zuerst den Solver ausführen oder eine Lösung auswählen."
        )
        st.info("Gehe zur Solver-Seite um eine Lösung zu berechnen.")
        # Dropdown-Menü für fertige Lösungen
        st.write("### Gespeicherte Lösungen laden")

        # Liste aller verfügbaren Lösungsdateien
        available_solutions = []
        if SOLUTION_DIR.exists():
            available_solutions = [f.stem for f in SOLUTION_DIR.glob("*.json")]
            available_solutions.sort()

        if available_solutions:
            selected_solution = st.selectbox(
                "Wähle eine gespeicherte Lösung:",
                options=[""] + available_solutions,
                index=0,
                help="Wähle eine Lösung aus dem Dropdown-Menü",
            )

            if selected_solution:
                try:
                    loaded_solution = solution.Solution.from_json_file(
                        selected_solution
                    )
                    st.session_state[SSN.solutions.name].append(loaded_solution)
                    st.success(f"Lösung '{selected_solution}' erfolgreich geladen!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Fehler beim Laden der Lösung: {e}")
        else:
            st.info("Keine gespeicherten Lösungen gefunden.")

        return
    sol = st.session_state[SSN.solutions.name][-1]

    st.write("### Objective Value")
    st.write(f"**{sol.objective_value}**")

    # Zeige aktive Constraints
    show_active_constraints(sol)

    # Constraint-Validierung anzeigen
    show_constraint_violations(sol)

    st.write("### Shift Plan")

    render_shift_plan_component(sol)

    st.write("### Vorherige Lösungen (absteigend)")

    for sol in reversed(st.session_state[SSN.solutions.name][:-1]):
        render_shift_plan_component(sol, read_only=True)
