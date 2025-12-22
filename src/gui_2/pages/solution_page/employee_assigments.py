from nicegui import ui

from ....solution import Solution


def emplyee_Assigments(solution: Solution):
    with ui.card().classes("w-full mb-4"):
        ui.label("Mitarbeiter-Zuordnung").classes("text-xl font-bold mb-2")

        days = sorted({day for (day, _, _) in solution.vars.keys()})
        shift_types = sorted({shift for (_, shift, _) in solution.vars.keys()})

        # Erstelle Spalten: Schichttyp + alle Tage
        columns = [
            {
                "name": "shift_type",
                "label": "Schichttyp",
                "field": "shift_type",
                "align": "left",
            }
        ]
        for day in days:
            columns.append(
                {
                    "name": f"day_{day}",
                    "label": f"Tag {day}",
                    "field": f"day_{day}",
                    "align": "left",
                }
            )

        # Erstelle Zeilen: eine Zeile pro Schichttyp
        rows = []
        for shift_type in shift_types:
            row = {
                "shift_type": f"Schicht {solution.instance.shift_types[shift_type].name}"
            }

            for day in days:
                assigned = [
                    solution.instance.employees[emp_uid].name
                    for emp_uid in solution.instance.employees.keys()
                    if solution.is_employee_assigned(day, shift_type, emp_uid)
                ]

                row[f"day_{day}"] = ", ".join(assigned) if assigned else "-"

            rows.append(row)

        ui.table(columns=columns, rows=rows, row_key="shift_type").classes("w-full")
