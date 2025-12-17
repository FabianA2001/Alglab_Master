from datetime import time
from pathlib import Path

import pandas as pd
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
        st.session_state[SSN.instance.name] = loaded_solution.instance
        st.success(
            f"Lösung '{st.session_state.solution_selectbox}' erfolgreich geladen!"
        )
        st.session_state[SSN.allow_resolve.name] = True
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
            force_assign_employees = []
            banned_employees = []
            for emp_id in sol.instance.employees:
                if sol.is_employee_assigned(day, shift_type_uid, emp_id):
                    assigned_employees.append(sol.instance.employees[emp_id].name)
            for emp_id in sol.instance.shifts[day][
                shift_type_uid
            ].assign_employee_day_shift:
                force_assign_employees.append(sol.instance.employees[emp_id].name)
            for emp_id in sol.instance.shifts[day][
                shift_type_uid
            ].ban_employee_day_shift:
                banned_employees.append(sol.instance.employees[emp_id].name)
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
                    "banned_employees": banned_employees,
                    "force_assigned_employees": force_assign_employees,
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

    solution_changes_response = my_component.my_component(
        f"shift_plan_component_{index}",
        render_option="shift_plan_solution",
        data=json.dumps(shift_plan_data),
        extra_options=json.dumps(extra_options),
    )

    if read_only:
        return
    st.markdown(f"The selected employee is: {solution_changes_response}")
    if solution_changes_response:
        st.session_state[SSN.changes_days.name] = set()
    changed_days = set()
    instance = sol.instance.model_copy(deep=True)
    submit_type_hard = True
    if solution_changes_response["submit_type"] == "soft":
        submit_type_hard = False
    elif solution_changes_response["submit_type"] == "hard":
        submit_type_hard = True
    if len(solution_changes_response["cover_weights"]) > 0:
        for day, shift_type_dict in solution_changes_response["cover_weights"].items():
            for shift_type, value in shift_type_dict.items():
                # TODO what about weight_above_preferred?
                instance.shifts[int(day)][
                    hash_string(shift_type)
                ].weight_below_preferred = int(value)
                changed_days.add(int(day))
        instance.name = instance.name + "_1"
        # does changing the instance refreash everything that the remaining changes do not happen?

    # TODO should I reset, considering I am showing everything in the frontend
    for key, shift_dict in instance.shifts.items():
        for type_uid, shift_detail in shift_dict.items():
            instance.shifts[key][type_uid].ban_employee_day_shift = set()
            instance.shifts[key][type_uid].assign_employee_day_shift = set()
    if len(solution_changes_response["added_employees"]) > 0 and submit_type_hard:
        for day, shift_type_dict in solution_changes_response[
            "added_employees"
        ].items():
            for shift_type, employees in shift_type_dict.items():
                for employee in employees:
                    instance.shifts[int(day)][
                        hash_string(shift_type)
                    ].assign_employee_day_shift.add(hash_string(employee))
                    changed_days.add(int(day))
        instance.name = instance.name + "_2"
    elif len(solution_changes_response["added_employees"]) > 0 and not submit_type_hard:
        for day, shift_type_dict in solution_changes_response[
            "added_employees"
        ].items():
            for shift_type, employees in shift_type_dict.items():
                for employee in employees:
                    # TODO instead of immediately giving it the value of 300 allow some how for changes
                    instance.shifts[int(day)][
                        hash_string(shift_type)
                    ].penalty_assigned_day_employee[hash_string(employee)] = 300
                    changed_days.add(int(day))

    if len(solution_changes_response["removed_employees"]) > 0 and submit_type_hard:
        for day, shift_type_dict in solution_changes_response[
            "removed_employees"
        ].items():
            for shift_type, employees in shift_type_dict.items():
                for employee in employees:
                    instance.shifts[int(day)][
                        hash_string(shift_type)
                    ].ban_employee_day_shift.add(hash_string(employee))
                    changed_days.add(int(day))
        instance.name = instance.name + "_3"
    elif (
        len(solution_changes_response["removed_employees"]) > 0 and not submit_type_hard
    ):
        for day, shift_type_dict in solution_changes_response[
            "removed_employees"
        ].items():
            for shift_type, employees in shift_type_dict.items():
                for employee in employees:
                    instance.shifts[int(day)][
                        hash_string(shift_type)
                    ].penalty_not_assigned_day_employee[hash_string(employee)] = 300
                    changed_days.add(int(day))

    st.session_state[SSN.instance.name] = instance
    if solution_changes_response:
        st.session_state[SSN.changes_days.name] = changed_days

    st.success("Instance updated with the removed employees.")
    st.session_state[SSN.allow_resolve.name] = True
    # TODO add reset parameters for employee add and remove
    return


def show_solution_employee_changes():
    if len(st.session_state[SSN.solutions.name]) < 2:
        st.info("Es sind mindestens zwei Lösungen erforderlich, um sie zu vergleichen.")
        return (None, [])
    all_columns = []
    solutions_list = []
    # bring the solutions into a more managable structure
    for i, sol in enumerate(reversed(st.session_state[SSN.solutions.name])):
        newer_solution = {"selected": {}, "deselected": {}}
        # TODO Test if the instance solutions belong to the same original instance more specifically
        if (
            sol.instance.number_of_days
            != st.session_state[SSN.solutions.name][-1].instance.number_of_days
        ):
            continue
        if len(sol.instance.shift_types) != len(
            st.session_state[SSN.solutions.name][-1].instance.shift_types
        ):
            continue
        if len(sol.instance.employees) != len(
            st.session_state[SSN.solutions.name][-1].instance.employees
        ):
            continue
        for keys, selected in sol.vars.items():
            shift_name = sol.instance.shift_types[keys[1]].name
            employee_name = sol.instance.employees[keys[2]].name
            if selected:
                if keys[0] not in newer_solution["selected"]:
                    newer_solution["selected"][keys[0]] = {}
                if shift_name not in newer_solution["selected"][keys[0]]:
                    newer_solution["selected"][keys[0]][shift_name] = []
                newer_solution["selected"][keys[0]][shift_name].append(employee_name)
            else:
                if keys[0] not in newer_solution["deselected"]:
                    newer_solution["deselected"][keys[0]] = {}
                if shift_name not in newer_solution["deselected"][keys[0]]:
                    newer_solution["deselected"][keys[0]][shift_name] = []
                newer_solution["deselected"][keys[0]][shift_name].append(employee_name)
        solutions_list.append(newer_solution)

    # Process the created structures
    all_rows = []
    # solutions_list all solutions dict
    for index, solution_dict in enumerate(solutions_list):
        # for the current solution the selected part
        solution_row = {}
        shifts_count_difference = 0
        for day, shift_dict in solution_dict["selected"].items():
            for shift_uid, employee_list in shift_dict.items():
                if index + 1 < len(solutions_list):
                    select_previous_solution_list = solutions_list[index + 1][
                        "deselected"
                    ][day][shift_uid]

                    solution_row[f"added_to_{day}_{shift_uid}"] = [
                        item
                        for item in employee_list
                        if item in select_previous_solution_list
                    ]
                    deseleted_current_solution_list = solution_dict["deselected"][day][
                        shift_uid
                    ]
                    seleted_previous_solution_list = solutions_list[index + 1][
                        "selected"
                    ][day][shift_uid]

                    solution_row[f"removed_from_{day}_{shift_uid}"] = [
                        item
                        for item in deseleted_current_solution_list
                        if item in seleted_previous_solution_list
                    ]

                    solution_row[f"employ_count_{day}_{shift_uid}"] = len(
                        employee_list
                    ) - len(seleted_previous_solution_list)
                    shifts_count_difference += solution_row[
                        f"employ_count_{day}_{shift_uid}"
                    ]

                    all_columns.append(f"added_to_{day}_{shift_uid}")
                    all_columns.append(f"removed_from_{day}_{shift_uid}")
                    all_columns.append(f"employ_count_{day}_{shift_uid}")
        solution_row["shifts_count_difference"] = shifts_count_difference
        all_rows.append(solution_row)

    return (pd.DataFrame(all_rows), all_columns)


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
    # TODO should must likly be removed because it breaks some functions for example with show_solution_employee_changes
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

    df, df_columns = show_solution_employee_changes()
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
    )

    if SSN.solutions.name in st.session_state and st.session_state[SSN.solutions.name]:
        sol = st.session_state[SSN.solutions.name][-1]

        # Calculate fulfillment metrics
        min_positive = sol.minimal_employee_positive_wishes_met()
        max_positive = sol.maximum_employee_positive_wishes_met()
        avg_positive = sol.average_employee_positive_wishes_met()

        min_negative = sol.minimal_employee_negative_wishes_met()
        max_negative = sol.maximum_employee_negative_wishes_met()
        avg_negative = sol.average_employee_negative_wishes_met()

        min_shift = sol.minimal_shift_fulfillment()
        max_shift = sol.maximum_shift_fulfillment()
        avg_shift = sol.average_shift_fulfillment()

        # Display the results in Streamlit
        st.title("Solution Fulfillment Metrics")

        st.header("Employee Positive Wishes Fulfillment")
        st.write(f"Minimal Fulfillment: {min_positive:.2%}")
        st.write(f"Maximum Fulfillment: {max_positive:.2%}")
        st.write(f"Average Fulfillment: {avg_positive:.2%}")

        st.header("Employee Negative Wishes Fulfillment")
        st.write(f"Minimal Fulfillment: {min_negative:.2%}")
        st.write(f"Maximum Fulfillment: {max_negative:.2%}")
        st.write(f"Average Fulfillment: {avg_negative:.2%}")

        st.header("Shift Fulfillment")
        st.write(f"Minimal Fulfillment: {min_shift:.2%}")
        st.write(f"Maximum Fulfillment: {max_shift:.2%}")
        st.write(f"Average Fulfillment: {avg_shift:.2%}")

        # Inside your main Streamlit app function
        median_positive = sol.median_employee_positive_wishes_met()
        median_negative = sol.median_employee_negative_wishes_met()

        st.header("Employee Positive Wishes Median")
        st.write(f"Median Fulfillment: {median_positive:.2%}")

        st.header("Employee Negative Wishes Median")
        st.write(f"Median Fulfillment: {median_negative:.2%}")
    else:
        st.warning("No solutions available in session state.")
