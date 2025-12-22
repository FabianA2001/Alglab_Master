"""Employee assignment view for shift scheduling solutions."""

from typing import Any, Dict, List

from nicegui import ui

from ....solution import Solution


def employee_assignments(solution: Solution) -> None:
    """
    Display employee assignments in a table format.

    Creates an interactive table showing which employees are assigned to which
    shifts on each day. Clicking on a cell shows detailed information.

    Args:
        solution: The Solution object containing shift assignments.
    """
    with ui.card().classes("w-full mb-4"):
        ui.label("Mitarbeiter-Zuordnung").classes("text-xl font-bold mb-2")

        days = _extract_days(solution)
        shift_types = _extract_shift_types(solution)

        columns = _build_table_columns(days)
        rows, shift_mapping = _build_table_rows(solution, days, shift_types)

        table = (
            ui.table(columns=columns, rows=rows, row_key="row_key")
            .classes("w-full")
            .props("flat hide-selected-banner")
        )

        # Add custom cell rendering with clickable elements
        table.add_slot(
            "body-cell",
            """
            <q-td :props="props" 
                  :class="props.col.name !== 'shift_type' ? 'cursor-pointer hover:bg-blue-50' : ''">
                <div v-if="props.col.name === 'shift_type'" class="text-weight-medium">
                    {{ props.value }}
                </div>
                <div v-else-if="props.value === '-'" class="text-grey-5 text-center">
                    —
                </div>
                <div v-else class="q-pa-xs" 
                     @click="() => $parent.$emit('cell_click', props.row.row_key, props.col.name)">
                    <q-badge v-for="(name, index) in props.value.split(', ')" 
                             :key="index"
                             color="primary" 
                             text-color="white"
                             class="q-ma-xs">
                        {{ name }}
                    </q-badge>
                </div>
            </q-td>
        """,
        )

        table.on(
            "cell_click",
            lambda e: _handle_cell_click(e.args[0], e.args[1], solution, shift_mapping),
        )


def _extract_days(solution: Solution) -> List[int]:
    """Extract and sort unique days from solution variables."""
    return sorted({day for (day, _, _) in solution.vars.keys()})


def _extract_shift_types(solution: Solution) -> List[Any]:
    """Extract and sort unique shift types from solution variables."""
    return sorted({shift for (_, shift, _) in solution.vars.keys()})


def _build_table_columns(days: List[int]) -> List[Dict[str, str]]:
    """
    Build table column definitions.

    Args:
        days: List of days to create columns for.

    Returns:
        List of column definitions for the table.
    """
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

    return columns


def _build_table_rows(
    solution: Solution, days: List[int], shift_types: List[Any]
) -> tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Build table row data and shift mapping.

    Args:
        solution: The Solution object containing shift assignments.
        days: List of days.
        shift_types: List of shift types.

    Returns:
        Tuple of (rows, shift_mapping) where rows is the table data and
        shift_mapping maps row keys to shift type IDs.
    """
    shift_mapping = {}
    rows = []

    for idx, shift_type in enumerate(shift_types):
        row_key = f"shift_{idx}"
        shift_mapping[row_key] = shift_type

        row = {
            "shift_type": f"Schicht {solution.instance.shift_types[shift_type].name}",
            "row_key": row_key,
        }

        for day in days:
            assigned = _get_assigned_employees(solution, day, shift_type)
            row[f"day_{day}"] = ", ".join(assigned) if assigned else "-"

        rows.append(row)

    return rows, shift_mapping


def _get_assigned_employees(solution: Solution, day: int, shift_type: Any) -> List[str]:
    """
    Get list of employee names assigned to a specific shift.

    Args:
        solution: The Solution object containing shift assignments.
        day: The day to check.
        shift_type: The shift type to check.

    Returns:
        List of employee names assigned to the shift.
    """
    return [
        solution.instance.employees[emp_uid].name
        for emp_uid in solution.instance.employees.keys()
        if solution.is_employee_assigned(day, shift_type, emp_uid)
    ]


def _handle_cell_click(
    row_key: str, col_name: str, solution: Solution, shift_mapping: Dict[str, Any]
) -> None:
    """
    Handle cell click events from the table.

    Args:
        row_key: The key identifying the row (shift type).
        col_name: The column name (e.g., 'day_1', 'day_2').
        solution: The Solution object containing shift assignments.
        shift_mapping: Mapping from row keys to shift type IDs.
    """
    # Ignore clicks on the shift type column
    if col_name == "shift_type":
        return

    day = int(col_name.replace("day_", ""))
    shift_type_id = shift_mapping[row_key]
    shift_name = solution.instance.shift_types[shift_type_id].name

    assigned_employees = _get_assigned_employees(solution, day, shift_type_id)

    _display_details_dialog(day, shift_name, assigned_employees)


def _display_details_dialog(
    day: int, shift_name: str, assigned_employees: List[str]
) -> None:
    """
    Display a dialog with shift assignment details.

    Args:
        day: The day number.
        shift_name: The name of the shift.
        assigned_employees: List of assigned employee names.
    """
    with ui.dialog() as dialog, ui.card():
        ui.label(f"Details: Tag {day}, Schicht {shift_name}").classes(
            "text-lg font-bold"
        )
        ui.separator()

        if assigned_employees:
            ui.label("Zugewiesene Mitarbeiter:").classes("font-semibold mt-2")
            for emp_name in assigned_employees:
                ui.label(f"• {emp_name}")
        else:
            ui.label("Keine Mitarbeiter zugewiesen").classes("text-gray-500")

        ui.button("Schließen", on_click=dialog.close).classes("mt-4")

    dialog.open()
