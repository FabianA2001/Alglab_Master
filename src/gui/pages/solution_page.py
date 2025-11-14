from datetime import time
from pathlib import Path

import streamlit as st

from ... import solution
from ...help_functions import compare_solutions, hash_string
from .component_solution import my_component
from .session_state_names import Session_state_Names as SSN
from .show_constraints import show_active_constraints, show_constraint_violations

SOLUTION_DIR = (
    Path(__file__).resolve().parent.parent.parent.parent / "data" / "solutions"
)


def on_change_solution():
    try:
        loaded_solution = solution.Solution.from_json_file(
            st.session_state.solution_selectbox
        )
        st.session_state[SSN.solutions.name].append(loaded_solution)
        st.success(
            f"Lösung '{st.session_state.solution_selectbox}' erfolgreich geladen!"
        )
    except Exception as e:
        st.error(f"Fehler beim Laden der Lösung: {e}")


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

    # create a list of employee names
    employee_names = []
    for employee in sol.instance.employees.values():
        employee_names.append(employee.name)

    return {
        "shift_types_info": shift_types_info,
        "num_days": sol.instance.number_of_days,
        "data": data,
        "employee_names": employee_names,
    }


def render_shift_plan_component(
    sol: solution.Solution, read_only: bool = False, index=0
):
    """Rendert die Custom HTML/JS Komponente für den Shift Plan"""
    import json

    # Konvertiere Lösung in JSON-Format
    shift_plan_data = solution_to_html_data(sol)
    extra_options = {"read_only": read_only}
    if "counter" not in st.session_state:
        st.session_state["counter"] = 0
    solution_changes_response = my_component.my_component(
        f"shift_plan_component_{index}",
        render_option="shift_plan_solution",
        data=json.dumps(shift_plan_data),
        extra_options=json.dumps(extra_options),
    )
    if st.button(
        "Reset Component",
        type="primary",
        disabled=st.session_state[SSN.solver_running.name],
        key="Reset_Component",
    ):
        st.rerun()

    if read_only:
        return
    st.markdown(f"The selected employee is: {solution_changes_response}")
    if "cover_weights" in solution_changes_response:
        instance = sol.instance.model_copy(deep=True)
        for day, shift_type_dict in solution_changes_response["cover_weights"].items():
            for shift_type, value in shift_type_dict.items():
                # TODO what about weight_above_preferred?
                instance.shifts[int(day)][
                    hash_string(shift_type)
                ].weight_below_preferred = int(value)
                instance.name = instance.name + "eddited_cover_requirements"
        st.session_state[SSN.instance.name] = instance
        st.success("Instance updated with new cover requirements from component.")
        st.session_state[SSN.allow_resolve.name] = True


def show_compare_solutions():
    if len(st.session_state[SSN.solutions.name]) < 2:
        st.info("Es sind mindestens zwei Lösungen erforderlich, um sie zu vergleichen.")
        return
    com = compare_solutions(
        st.session_state[SSN.solutions.name][-2],
        st.session_state[SSN.solutions.name][-1],
        include_details=True,
    )

    # Zeige Zusammenfassung in einer Tabelle
    st.write("### Lösungsvergleich")
    summary_data = {
        "Metrik": ["Mitarbeiter mit Änderungen", "Gesamtzahl geänderter Tage"],
        "Wert": [
            com.get("employees_with_changes", 0),
            com.get("total_changed_days", 0),
        ],
    }
    st.table(summary_data)

    # Zeige Details pro Mitarbeiter, falls vorhanden
    if "per_employee_changes" in com and com["per_employee_changes"]:
        st.write("#### Änderungen pro Mitarbeiter")
        employee_data = []
        for emp_uid, emp_data in com["per_employee_changes"].items():
            employee_data.append(
                {
                    "Mitarbeiter ID": emp_uid,
                    "Name": emp_data.get("name", "Unbekannt"),
                    "Anzahl geänderter Tage": emp_data.get("num_changed_days", 0),
                }
            )
        st.dataframe(employee_data, use_container_width=True)

    # Zeige Details pro Tag, falls vorhanden
    if "per_day_changes" in com and com["per_day_changes"]:
        st.write("#### Änderungen pro Tag")
        day_data = []
        for day, count in sorted(com["per_day_changes"].items()):
            if count > 0:  # Nur Tage mit Änderungen anzeigen
                day_data.append({"Tag": day, "Anzahl Änderungen": count})
        if day_data:
            st.dataframe(day_data, use_container_width=True)


def show():
    st.title("✅ Solution")
    # Check if solution exists in session state
    # TODO Discuss if always show solution selector or only when no solution in session state
    available_solutions = []
    if SOLUTION_DIR.exists():
        available_solutions = [f.stem for f in SOLUTION_DIR.glob("*.json")]
        available_solutions.sort()

    if available_solutions:
        st.selectbox(
            "Wähle eine gespeicherte Lösung:",
            options=[""] + available_solutions,
            key="solution_selectbox",
            index=0,
            help="Wähle eine Lösung aus dem Dropdown-Menü",
            on_change=on_change_solution,
        )

    else:
        st.info("Keine gespeicherten Lösungen gefunden.")
        return

    if (
        SSN.solutions.name not in st.session_state
        or st.session_state[SSN.solutions.name] == []
    ):
        st.warning(
            "Keine Lösung verfügbar. Bitte zuerst den Solver ausführen oder eine Lösung auswählen."
        )
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
    for i, sol in enumerate(reversed(st.session_state[SSN.solutions.name][:-1])):
        render_shift_plan_component(sol, read_only=True, index=i + 1)

    show_compare_solutions()
