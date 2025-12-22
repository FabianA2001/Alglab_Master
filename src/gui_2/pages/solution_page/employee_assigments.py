from nicegui import ui

from ....solution import Solution


def emplyee_Assigments(solution: Solution):
    with ui.card().classes("w-full mb-4"):
        ui.label("Mitarbeiter-Zuordnung").classes("text-xl font-bold mb-2")

        days = sorted({day for (day, _, _) in solution.vars.keys()})

        with ui.expansion("Zuordnung pro Tag", icon="calendar_today").classes("w-full"):
            for day in days:
                assigned = [
                    solution.instance.employees[emp_uid].name
                    for (d, _, emp_uid), value in solution.vars.items()
                    if d == day and value == 1
                ]

                with ui.expansion(
                    f"Tag {day} ({len(assigned)} Mitarbeiter)", icon="schedule"
                ):
                    if assigned:
                        for emp_name in assigned:
                            ui.label(f"• {emp_name}")
                    else:
                        ui.label("Niemand eingeteilt").classes("text-gray-500 italic")
