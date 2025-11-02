from pathlib import Path

import pandas as pd
import streamlit as st

from ... import solution

SOLUTION_DIR = (
    Path(__file__).resolve().parent.parent.parent.parent / "data" / "solutions"
)


def soluation_to_dataframe(solution: solution.Solution) -> pd.DataFrame:
    # Diese Funktion sollte die Lösung in ein DataFrame umwandeln
    days = [day for day in range(solution.instance.number_of_days)]
    shift_types = [
        shift_type.name for shift_type in solution.instance.shift_types.values()
    ]
    # blank_data = {day: [[] for _ in shift_types] for day in days}
    data = []
    for shift_type_uid in solution.instance.shift_types:
        row = []
        for day in days:
            assigned_employees = []
            for emp_id in solution.instance.employees:
                if solution.is_employee_assigned(day, shift_type_uid, emp_id):
                    assigned_employees.append(solution.instance.employees[emp_id].name)
            row.append(assigned_employees)
        data.append(row)

    df = pd.DataFrame(data, index=shift_types)

    return df


def show():
    st.title("✅ Solution")
    # Check if solution exists in session state
    if "solution" not in st.session_state:
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
                    st.session_state["solution"] = loaded_solution
                    st.success(f"Lösung '{selected_solution}' erfolgreich geladen!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Fehler beim Laden der Lösung: {e}")
        else:
            st.info("Keine gespeicherten Lösungen gefunden.")

        return

    sol = st.session_state["solution"]

    st.write("### Objective Value")
    st.write(f"**{sol.objective_value}**")
    st.write("### Shift Plan")
    st.dataframe(soluation_to_dataframe(sol), key="shiftplan")
