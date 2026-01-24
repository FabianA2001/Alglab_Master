"""Employee assignment view for shift scheduling solutions."""

from typing import Any, Dict, List

from nicegui import ui

from ....solution import Solution
from ... import state
from . import components

# Color constants for cell background based on employee count
COLOR_CORRECT_COUNT = "background-color: #d1fae5;"  # Green
COLOR_TOO_FEW = "background-color: #fee2e2;"  # Red
COLOR_TOO_MANY = "background-color: #fed7aa;"  # Orange

# Weight adjustment constant for soft buttons
SOFT_WEIGHT_ADJUSTMENT = 10


def employee_assignments(
    solution: Solution,
    current_week: dict,
    comparison_refresh_callback=None,
    commit_callback=None,
    employee_change_callback=None,
) -> None:
    """
    Display employee assignments in a table format.

    Creates an interactive table showing which employees are assigned to which
    shifts on each day. Clicking on a cell shows detailed information.

    Args:
        solution: The Solution object containing shift assignments.
        current_week: Dictionary mit 'value' key für die aktuelle Woche (shared)
        comparison_refresh_callback: Optional callback to refresh comparison table
        commit_callback: Optional callback to commit changes to state
        employee_change_callback: Optional callback to track changed employees
    """
    with ui.card().classes("w-full mb-4"):
        ui.label("Mitarbeiter-Zuordnung").classes("text-xl font-bold mb-2")

        all_days = _extract_days(solution)
        shift_types = _extract_shift_types(solution)

        # Calculate weeks (7 days per week)
        num_weeks = (len(all_days) + 6) // 7  # Round up
        weeks = []
        for week_idx in range(num_weeks):
            start_idx = week_idx * 7
            end_idx = min(start_idx + 7, len(all_days))
            week_days = all_days[start_idx:end_idx]
            weeks.append((week_idx + 1, week_days))

        # Capture callbacks outside of refreshable function
        captured_commit_callback = commit_callback
        captured_employee_change_callback = employee_change_callback

        @ui.refreshable
        def render_table():
            """Render the table for the current week."""
            week_num, days = weeks[current_week["value"]]

            ui.label(f"Woche {week_num} (Tage {days[0]} - {days[-1]})").classes(
                "text-lg font-semibold mb-2"
            )

            columns = _build_table_columns(days)
            rows, shift_mapping = _build_table_rows(solution, days, shift_types)

            table = (
                ui.table(columns=columns, rows=rows, row_key="row_key")
                .classes("w-full")
                .props("flat hide-selected-banner")
            )

            # Add custom cell rendering with clickable elements and color coding
            table.add_slot(
                "body-cell",
                """
                <q-td :props="props">
                    <div v-if="props.col.name === 'shift_type'" class="text-weight-medium">
                        {{ props.value }}
                    </div>
                    <div v-else-if="props.value === '-'" class="text-grey-5 text-center cursor-pointer q-pa-xs"
                         :style="props.row['_color_' + props.col.name] || ''"
                         @click="() => $parent.$emit('cell_click', props.row.row_key, props.col.name)">
                        —
                    </div>
                    <div v-else class="q-pa-xs cursor-pointer" 
                         :style="props.row['_color_' + props.col.name] || ''"
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

            # Use captured callbacks in closure
            def handle_cell_click(e):
                _display_details_dialog(
                    e.args[0],
                    e.args[1],
                    solution,
                    shift_mapping,
                    captured_commit_callback,
                    captured_employee_change_callback,
                )

            table.on("cell_click", handle_cell_click)

        # Week navigation
        if num_weeks > 1:
            with ui.row().classes("gap-2 items-center mb-4"):

                def on_week_change(new_value):
                    """Handle week change and refresh both tables."""
                    current_week.update(value=new_value)
                    render_table.refresh()
                    if comparison_refresh_callback:
                        try:
                            comparison_refresh_callback()
                        except (RuntimeError, AttributeError):
                            pass

                ui.button(
                    icon="chevron_left",
                    on_click=lambda: on_week_change(max(0, current_week["value"] - 1)),
                ).props("flat").bind_enabled_from(
                    current_week, "value", lambda v: v > 0
                )

                ui.label().bind_text_from(
                    current_week,
                    "value",
                    lambda v: f"Woche {weeks[v][0]} von {num_weeks}",
                ).classes("font-medium")

                ui.button(
                    icon="chevron_right",
                    on_click=lambda: on_week_change(
                        min(num_weeks - 1, current_week["value"] + 1)
                    ),
                ).props("flat").bind_enabled_from(
                    current_week, "value", lambda v: v < num_weeks - 1
                )

        # Render table
        render_table()

        # Color legend
        with ui.row().classes("mt-4 gap-4"):
            ui.label("Legende:").classes("font-semibold")
            with ui.row().classes("gap-2 items-center"):
                ui.element("div").classes("w-6 h-6 rounded").style(COLOR_CORRECT_COUNT)
                ui.label("Korrekte Anzahl")
            with ui.row().classes("gap-2 items-center"):
                ui.element("div").classes("w-6 h-6 rounded").style(COLOR_TOO_FEW)
                ui.label("Zu wenige Mitarbeiter")
            with ui.row().classes("gap-2 items-center"):
                ui.element("div").classes("w-6 h-6 rounded").style(COLOR_TOO_MANY)
                ui.label("Zu viele Mitarbeiter")


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
    Build table row data and shift mapping with color coding.

    Rows include cell background colors based on employee count vs. preferred count:
    - Green: Correct number of employees
    - Red: Too few employees
    - Orange: Too many employees

    Args:
        solution: The Solution object containing shift assignments.
        days: List of days to include in the table.
        shift_types: List of shift type IDs.

    Returns:
        Tuple of (rows, shift_mapping) where:
        - rows: List of row dictionaries with data and color information
        - shift_mapping: Maps row keys to shift type IDs
    """
    shift_mapping = {}
    rows = []

    for idx, shift_type in enumerate(shift_types):
        row_key = f"shift_{idx}"
        shift_mapping[row_key] = shift_type

        shift_type_obj = solution.instance.shift_types.get(shift_type)
        if shift_type_obj is None:
            continue

        row = {
            "shift_type": f"Schicht {shift_type_obj.name}",
            "row_key": row_key,
        }

        for day in days:
            assigned = _get_assigned_employees(solution, day, shift_type)
            row[f"day_{day}"] = ", ".join(assigned) if assigned else "-"

            # Add cell background color based on employee count vs. preferred
            shift_obj = solution.instance.shifts.get(day, {}).get(shift_type)
            if shift_obj:
                preferred_count = shift_obj.preffert_number_employees
                if preferred_count > 0:
                    actual_count = len(assigned)

                    if actual_count == preferred_count:
                        row[f"_color_day_{day}"] = COLOR_CORRECT_COUNT
                    elif actual_count < preferred_count:
                        row[f"_color_day_{day}"] = COLOR_TOO_FEW
                    else:
                        row[f"_color_day_{day}"] = COLOR_TOO_MANY

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
    result = []
    for emp_uid in solution.instance.employees.keys():
        if solution.is_employee_assigned(day, shift_type, emp_uid):
            emp = solution.instance.employees.get(emp_uid)
            if emp:
                result.append(emp.name)
    return result


def _display_details_dialog(
    row_key: str,
    col_name: str,
    solution: Solution,
    shift_mapping: Dict[str, Any],
    commit_callback=None,
    employee_change_callback=None,
) -> None:
    """
    Handle cell click events and display a dialog with shift assignment details.

    Args:
        row_key: The key identifying the row (shift type).
        col_name: The column name (e.g., 'day_1', 'day_2').
        solution: The Solution object containing shift assignments.
        shift_mapping: Mapping from row keys to shift type IDs.
        commit_callback: Optional callback to commit changes to state.
        employee_change_callback: Optional callback to track changed employees.
    """
    # Ignore clicks on the shift type column
    if col_name == "shift_type":
        return

    day = int(col_name.replace("day_", ""))
    shift_type_id = shift_mapping.get(row_key)
    if shift_type_id is None:
        ui.notify("Schichttyp nicht gefunden.", type="negative")
        return

    shift_type_obj = solution.instance.shift_types.get(shift_type_id)
    if shift_type_obj is None:
        ui.notify("Schichttyp nicht gefunden.", type="negative")
        return
    shift_name = shift_type_obj.name

    assigned_employees = _get_assigned_employees(solution, day, shift_type_id)
    actual_count = len(assigned_employees)

    # Get shift object for preferred count and weight
    shift_obj = solution.instance.shifts.get(day, {}).get(shift_type_id)
    if not shift_obj:
        ui.notify("Schichtdaten nicht gefunden.", type="negative")
        return

    preferred_count = shift_obj.preffert_number_employees
    weight_below = shift_obj.weight_below_preferred

    with ui.dialog() as dialog, ui.card().classes("min-w-96"):
        _render_dialog_header(day, shift_name, actual_count, preferred_count)
        ui.separator()
        _render_employee_list(assigned_employees)

        # Employee add/remove section
        ui.separator().classes("my-4")
        _render_employee_modification_section(
            solution,
            shift_obj,
            day,
            shift_type_id,
            shift_name,
            dialog,
            commit_callback,
            employee_change_callback,
        )

        # Weight adjustment section
        if preferred_count > 0:
            ui.separator().classes("my-4")
            _render_weight_adjustment_section(
                solution,
                shift_obj,
                day,
                shift_type_id,
                shift_name,
                weight_below,
                dialog,
                commit_callback,
            )

        ui.button("Schließen", on_click=dialog.close).classes("mt-4")

    dialog.open()


def _render_dialog_header(
    day: int, shift_name: str, actual_count: int, preferred_count: int
) -> None:
    """Render the dialog header with shift details and employee count."""
    ui.label(f"Details: Tag {day}, Schicht {shift_name}").classes("text-lg font-bold")

    # Show employee count ratio if preferred count is set
    if preferred_count > 0:
        ratio_text = f"Belegung: {actual_count}/{preferred_count}"
        color_class = (
            "text-green-600"
            if actual_count == preferred_count
            else "text-red-600"
            if actual_count < preferred_count
            else "text-orange-600"
        )
        ui.label(ratio_text).classes(f"{color_class} font-semibold")


def _render_employee_list(assigned_employees: List[str]) -> None:
    """Render the list of assigned employees."""
    if assigned_employees:
        ui.label("Zugewiesene Mitarbeiter:").classes("font-semibold mt-2")
        for emp_name in assigned_employees:
            ui.label(f"• {emp_name}")
    else:
        ui.label("Keine Mitarbeiter zugewiesen").classes("text-gray-500")


def _render_employee_modification_section(
    solution: Solution,
    shift_obj: Any,
    day: int,
    shift_type_id: Any,
    shift_name: str,
    dialog: Any,
    commit_callback=None,
    employee_change_callback=None,
) -> None:
    """
    Render the employee add/remove section with dropdowns and soft/hard buttons.

    Layout:
    Löschen | Hinzufügen
    dropdown | dropdown
    button(soft) | button(soft)
    button(hard) | button(hard)
    """
    ui.label("Mitarbeiter verwalten").classes("font-semibold")

    # Get all employees
    all_employees = {
        emp_uid: emp.name for emp_uid, emp in solution.instance.employees.items()
    }

    # Get currently assigned employees for the remove dropdown
    assigned_emp_uids = [
        emp_uid
        for emp_uid in solution.instance.employees.keys()
        if solution.is_employee_assigned(day, shift_type_id, emp_uid)
    ]

    # Get unassigned employees for the add dropdown
    unassigned_emp_uids = [
        emp_uid
        for emp_uid in solution.instance.employees.keys()
        if not solution.is_employee_assigned(day, shift_type_id, emp_uid)
    ]

    with ui.grid(columns=2).classes("w-full gap-4 mt-2"):
        # Left column: Remove employee
        with ui.column().classes("gap-2"):
            ui.label("Löschen").classes("font-medium")

            remove_dropdown = (
                ui.select(
                    options={uid: all_employees[uid] for uid in assigned_emp_uids},
                    label="Mitarbeiter auswählen",
                    with_input=True,
                )
                .classes("w-full")
                .props("outlined dense")
            )

            def remove_soft() -> None:
                """Soft remove: Increase penalty for assigning this employee."""
                selected_uid = remove_dropdown.value
                if selected_uid is None:
                    ui.notify("Bitte wählen Sie einen Mitarbeiter aus", type="warning")
                    return

                # Increase penalty_assigned_day_employee (auf Arbeitskopie)
                current_penalty = shift_obj.penalty_assigned_day_employee.get(
                    selected_uid, 0
                )
                shift_obj.penalty_assigned_day_employee[selected_uid] = (
                    current_penalty + SOFT_WEIGHT_ADJUSTMENT
                )

                # Markiere Tag als geändert
                state.add_changed_day(day)
                components.refresh_changed_days()

                # Tracke veränderten Mitarbeiter
                if employee_change_callback:
                    employee_change_callback(selected_uid)

                emp_name = all_employees.get(selected_uid, "Unbekannt")
                ui.notify(
                    f"Soft: Strafe für {emp_name} erhöht auf {current_penalty + SOFT_WEIGHT_ADJUSTMENT}",
                    type="positive",
                )

                # Übernehme Änderungen in den State
                if commit_callback:
                    commit_callback(False)

            def remove_hard() -> None:
                """Hard remove: Add employee to ban list."""
                selected_uid = remove_dropdown.value
                if selected_uid is None:
                    ui.notify("Bitte wählen Sie einen Mitarbeiter aus", type="warning")
                    return

                # Füge zur Sperrliste hinzu (auf Arbeitskopie)
                shift_obj.ban_employee_day_shift.add(selected_uid)

                # Markiere Tag als geändert
                state.add_changed_day(day)
                components.refresh_changed_days()

                # Tracke veränderten Mitarbeiter
                if employee_change_callback:
                    employee_change_callback(selected_uid)

                emp_name = all_employees.get(selected_uid, "Unbekannt")
                ui.notify(
                    f"Hard: {emp_name} wurde zur Sperrliste hinzugefügt",
                    type="positive",
                )

                # Übernehme Änderungen in den State
                if commit_callback:
                    commit_callback()

                dialog.close()

            # HACK disable soft
            # ui.button("Soft", on_click=remove_soft).classes("w-full").props(
            #     "outline color=orange"
            # )
            ui.button("Löschen", on_click=remove_hard).classes("w-full").props(
                "outline color=red"
            )

        # Right column: Add employee
        with ui.column().classes("gap-2"):
            ui.label("Hinzufügen").classes("font-medium")

            add_dropdown = (
                ui.select(
                    options={uid: all_employees[uid] for uid in unassigned_emp_uids},
                    label="Mitarbeiter auswählen",
                    with_input=True,
                )
                .classes("w-full")
                .props("outlined dense")
            )

            def add_soft() -> None:
                """Soft add: Decrease penalty for not assigning this employee."""
                selected_uid = add_dropdown.value
                if selected_uid is None:
                    ui.notify("Bitte wählen Sie einen Mitarbeiter aus", type="warning")
                    return

                # Increase penalty_not_assigned_day_employee (auf Arbeitskopie)
                current_penalty = shift_obj.penalty_not_assigned_day_employee.get(
                    selected_uid, 0
                )
                shift_obj.penalty_not_assigned_day_employee[selected_uid] = (
                    current_penalty + SOFT_WEIGHT_ADJUSTMENT
                )

                # Markiere Tag als geändert
                state.add_changed_day(day)
                components.refresh_changed_days()

                # Tracke veränderten Mitarbeiter
                if employee_change_callback:
                    employee_change_callback(selected_uid)

                emp_name = all_employees.get(selected_uid, "Unbekannt")
                ui.notify(
                    f"Soft: Strafe für Nicht-Zuweisung von {emp_name} erhöht auf {current_penalty + SOFT_WEIGHT_ADJUSTMENT}",
                    type="positive",
                )

                # Übernehme Änderungen in den State
                if commit_callback:
                    commit_callback(False)

            def add_hard() -> None:
                """Hard add: Add employee to assignment list."""
                selected_uid = add_dropdown.value
                if selected_uid is None:
                    ui.notify("Bitte wählen Sie einen Mitarbeiter aus", type="warning")
                    return

                # Füge zur Zuweisungsliste hinzu (auf Arbeitskopie)
                shift_obj.assign_employee_day_shift.add(selected_uid)

                # Markiere Tag als geändert
                state.add_changed_day(day)
                components.refresh_changed_days()

                # Tracke veränderten Mitarbeiter
                if employee_change_callback:
                    employee_change_callback(selected_uid)

                emp_name = all_employees.get(selected_uid, "Unbekannt")
                ui.notify(
                    f"Hard: {emp_name} wurde zur Zuweisungsliste hinzugefügt",
                    type="positive",
                )

                # Übernehme Änderungen in den State
                if commit_callback:
                    commit_callback()

                dialog.close()

            # HACK disable soft
            # ui.button("Soft", on_click=add_soft).classes("w-full").props(
            #     "outline color=orange"
            # )
            ui.button("Hinzufügen", on_click=add_hard).classes("w-full").props(
                "outline color=green"
            )


def _render_weight_adjustment_section(
    solution: Solution,
    shift_obj: Any,
    day: int,
    shift_type_id: Any,
    shift_name: str,
    weight_below: int,
    dialog: Any,
    commit_callback=None,
) -> None:
    """Render the weight adjustment section with input and update button."""
    ui.label("Instanz-Anpassungen").classes("font-semibold")

    weight_input = (
        ui.number(
            label="Gewicht bei Unterbesetzung",
            value=weight_below,
            min=0,
            step=1,
        )
        .classes("w-full mt-2")
        .props("outlined dense")
    )

    def update_weight() -> None:
        """Update the weight_below_preferred value in the instance."""
        new_weight = int(weight_input.value)
        # Setze neues Gewicht (auf Arbeitskopie)
        shift_obj.weight_below_preferred = new_weight

        # Markiere Tag als geändert
        state.add_changed_day(day)
        components.refresh_changed_days()

        ui.notify(
            f"Gewicht für Tag {day}, Schicht {shift_name} aktualisiert: {new_weight}",
            type="positive",
        )

        # Übernehme Änderungen in den State
        if commit_callback:
            commit_callback()

        dialog.close()

    ui.button("Gewicht aktualisieren", on_click=update_weight).classes("mt-2").props(
        "color=primary"
    )
