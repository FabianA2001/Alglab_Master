"""Comparison view for comparing two solutions."""

from typing import Any, Callable, Dict, List, Optional, Tuple

from nicegui import ui

from ....help_functions import compare_solutions
from ....solution import Solution


def render_solution_comparison(
    solution_a: Solution,
    solution_b: Solution,
    current_week: dict,
    register_refresh_callback: Optional[Callable] = None,
) -> None:
    """
    Rendert eine Vergleichsansicht zweier Solutions.

    Args:
        solution_a: Erste (Haupt-)Solution
        solution_b: Zweite Solution zum Vergleich
        current_week: Dictionary mit 'value' key für die aktuelle Woche (shared)
        register_refresh_callback: Optional callback to register refresh function
    """
    # Vergleich durchführen
    comparison_result = compare_solutions(solution_a, solution_b, include_details=True)

    with ui.card().classes("w-full mb-4"):
        ui.label("Lösungsvergleich").classes("text-xl font-bold mb-2")

        # Zusammenfassung
        with ui.row().classes("gap-4 mb-4"):
            with ui.card().classes("bg-blue-50"):
                ui.label(f"{comparison_result['employees_with_changes']}").classes(
                    "text-2xl font-bold text-blue-700"
                )
                ui.label("Mitarbeiter mit Änderungen").classes("text-sm")

            with ui.card().classes("bg-orange-50"):
                ui.label(f"{comparison_result['total_changed_days']}").classes(
                    "text-2xl font-bold text-orange-700"
                )
                ui.label("Gesamt geänderte Zuweisungen").classes("text-sm")

        # Shift-Tabelle mit Änderungen
        ui.label("Schicht-Änderungen (Ansicht: Lösung B)").classes(
            "text-lg font-semibold mt-4 mb-2"
        )
        ui.label("Markierte Zellen zeigen Änderungen gegenüber Lösung A").classes(
            "text-sm text-gray-600 mb-2"
        )

        _render_comparison_table(
            solution_a,
            solution_b,
            comparison_result,
            current_week,
            register_refresh_callback,
        )


def _render_comparison_table(
    solution_a: Solution,
    solution_b: Solution,
    comparison_result: dict,
    current_week: dict,
    register_refresh_callback: Optional[Callable] = None,
) -> None:
    """
    Rendert die Vergleichstabelle mit markierten Änderungen.

    Args:
        solution_a: Erste Solution (Referenz)
        solution_b: Zweite Solution (wird angezeigt)
        comparison_result: Ergebnis von compare_solutions
        current_week: Dictionary mit 'value' key für die aktuelle Woche (shared)
        register_refresh_callback: Optional callback to register refresh function
    """
    all_days = _extract_days(solution_b)
    shift_types = _extract_shift_types(solution_b)

    # Calculate weeks (7 days per week) - same logic as employee_assignments
    num_weeks = (len(all_days) + 6) // 7  # Round up
    weeks = []
    for week_idx in range(num_weeks):
        start_idx = week_idx * 7
        end_idx = min(start_idx + 7, len(all_days))
        week_days = all_days[start_idx:end_idx]
        weeks.append((week_idx + 1, week_days))

    @ui.refreshable
    def render_table():
        """Render the comparison table for the current week."""
        week_num, days = weeks[current_week["value"]]

        ui.label(f"Woche {week_num} (Tage {days[0]} - {days[-1]})").classes(
            "text-lg font-semibold mb-2"
        )

        columns = _build_table_columns(days)
        rows, shift_mapping, change_info = _build_comparison_rows(
            solution_a, solution_b, days, shift_types
        )

        table = (
            ui.table(columns=columns, rows=rows, row_key="row_key")
            .classes("w-full")
            .props("flat hide-selected-banner")
        )

        # Custom cell rendering mit Hervorhebung von Änderungen
        table.add_slot(
            "body-cell",
            """
            <q-td :props="props">
                <div v-if="props.col.name === 'shift_type'" class="text-weight-medium">
                    {{ props.value }}
                </div>
                <div v-else-if="props.value === '-'" class="text-grey-5 text-center">
                    —
                </div>
                <div v-else class="q-pa-xs cursor-pointer" 
                     :style="props.row['_color_' + props.col.name] || ''"
                     @click="() => $parent.$emit('cell_click', props.row.row_key, props.col.name)">
                    <q-badge v-for="(badge, index) in props.row['_badges_' + props.col.name]" 
                             :key="index"
                             :color="badge.color" 
                             text-color="white"
                             class="q-ma-xs">
                        {{ badge.name }}
                    </q-badge>
                </div>
            </q-td>
        """,
        )

        table.on(
            "cell_click",
            lambda e: _display_change_dialog(
                e.args[0], e.args[1], solution_a, solution_b, shift_mapping, change_info
            ),
        )

    # Register refresh function if callback provided
    if register_refresh_callback:
        register_refresh_callback(render_table.refresh)

    # Render table
    render_table()

    # Legende
    with ui.row().classes("mt-4 gap-4"):
        ui.label("Legende:").classes("font-semibold")
        with ui.row().classes("gap-2 items-center"):
            ui.element("div").classes("w-6 h-6 rounded").style(
                "background-color: #fef3c7;"
            )
            ui.label("Änderungen in dieser Schicht")


def _extract_days(solution: Solution) -> List[int]:
    """Extract and sort unique days from solution variables."""
    return sorted({day for (day, _, _) in solution.vars.keys()})


def _extract_shift_types(solution: Solution) -> List[Any]:
    """Extract and sort unique shift types from solution variables."""
    return sorted({shift for (_, shift, _) in solution.vars.keys()})


def _build_table_columns(days: List[int]) -> List[Dict[str, str]]:
    """Build table column definitions."""
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


def _build_comparison_rows(
    solution_a: Solution,
    solution_b: Solution,
    days: List[int],
    shift_types: List[Any],
) -> Tuple[List[Dict[str, Any]], Dict[str, Any], Dict[tuple[str, str], Dict]]:
    """
    Build table rows with change information.

    Returns:
        Tuple of (rows, shift_mapping, change_info) where:
        - rows: Table row data with badge information
        - shift_mapping: Maps row keys to shift type IDs
        - change_info: Maps (row_key, col_name) to change details
    """
    shift_mapping = {}
    change_info = {}
    rows = []

    for idx, shift_type in enumerate(shift_types):
        row_key = f"shift_{idx}"
        shift_mapping[row_key] = shift_type

        row = {
            "shift_type": f"Schicht {solution_b.instance.shift_types[shift_type].name}",
            "row_key": row_key,
        }

        for day in days:
            col_name = f"day_{day}"

            # Get employees in both solutions
            employees_a = _get_assigned_employees_dict(solution_a, day, shift_type)
            employees_b = _get_assigned_employees_dict(solution_b, day, shift_type)

            # Finde Änderungen
            all_employees = set(employees_a.keys()) | set(employees_b.keys())
            changes = []

            for emp_uid in all_employees:
                was_assigned = emp_uid in employees_a
                is_assigned = emp_uid in employees_b

                if was_assigned != is_assigned:
                    emp_name = (
                        employees_b.get(emp_uid)
                        or employees_a.get(emp_uid)
                        or str(emp_uid)
                    )
                    changes.append(
                        {
                            "emp_uid": emp_uid,
                            "emp_name": emp_name,
                            "was_assigned": was_assigned,
                            "is_assigned": is_assigned,
                        }
                    )

            # Erstelle Badge-Informationen
            badges = []
            for emp_uid in employees_b.keys():
                emp_name = employees_b[emp_uid]
                # Grün wenn neu hinzugefügt, normal wenn unverändert
                color = "green" if emp_uid not in employees_a else "primary"
                badges.append({"name": emp_name, "color": color})

            # Füge entfernte Mitarbeiter als rote Badges hinzu
            for emp_uid in employees_a.keys():
                if emp_uid not in employees_b:
                    emp_name = employees_a[emp_uid]
                    badges.append({"name": f"{emp_name} (entfernt)", "color": "red"})

            row[f"_badges_{col_name}"] = badges  # type: ignore
            row[col_name] = "data"  # Placeholder

            # Highlight wenn Änderungen vorhanden
            if changes:
                row[f"_color_{col_name}"] = "background-color: #fef3c7;"
                change_info[(row_key, col_name)] = {
                    "changes": changes,
                    "employees_a": employees_a,
                    "employees_b": employees_b,
                }

        rows.append(row)

    return rows, shift_mapping, change_info


def _get_assigned_employees_dict(
    solution: Solution, day: int, shift_type: Any
) -> Dict[int, str]:
    """
    Get dictionary of assigned employees (uid -> name).

    Args:
        solution: The Solution object
        day: The day to check
        shift_type: The shift type to check

    Returns:
        Dictionary mapping employee UID to name
    """
    result = {}
    for emp_uid in solution.instance.employees.keys():
        if solution.is_employee_assigned(day, shift_type, emp_uid):
            result[emp_uid] = solution.instance.employees[emp_uid].name
    return result


def _display_change_dialog(
    row_key: str,
    col_name: str,
    solution_a: Solution,
    solution_b: Solution,
    shift_mapping: Dict[str, Any],
    change_info: Dict[tuple[str, str], Dict],
) -> None:
    """
    Display a dialog showing the changes for a specific shift.

    Args:
        row_key: The row key (shift type)
        col_name: The column name (day)
        solution_a: First solution
        solution_b: Second solution
        shift_mapping: Mapping from row keys to shift type IDs
        change_info: Dictionary with change information
    """
    if col_name == "shift_type":
        return

    day = int(col_name.replace("day_", ""))
    shift_type_id = shift_mapping[row_key]
    shift_name = solution_b.instance.shift_types[shift_type_id].name

    info_key = (row_key, col_name)
    info = change_info.get(info_key)

    with ui.dialog() as dialog, ui.card().classes("min-w-96"):
        ui.label(f"Änderungen: Tag {day}, Schicht {shift_name}").classes(
            "text-lg font-bold mb-4"
        )

        if info and info.get("changes"):
            ui.label(f"{len(info['changes'])} Änderung(en) gefunden:").classes(
                "font-semibold mb-2"
            )

            for change in info["changes"]:
                with ui.card().classes("mb-2 bg-gray-50"):
                    emp_name = change["emp_name"]

                    if change["is_assigned"] and not change["was_assigned"]:
                        # Hinzugefügt
                        with ui.row().classes("items-center gap-2"):
                            ui.icon("add_circle").props("color=green")
                            ui.label(f"{emp_name}").classes("font-semibold")
                        ui.label("Neu zugewiesen").classes("text-sm text-green-700")

                    elif change["was_assigned"] and not change["is_assigned"]:
                        # Entfernt
                        with ui.row().classes("items-center gap-2"):
                            ui.icon("remove_circle").props("color=red")
                            ui.label(f"{emp_name}").classes("font-semibold")
                        ui.label("Zuweisung entfernt").classes("text-sm text-red-700")

            # Zeige auch die finalen Listen
            ui.separator().classes("my-4")

            with ui.row().classes("w-full gap-4"):
                with ui.column().classes("flex-1"):
                    ui.label("Lösung A:").classes("font-semibold text-sm")
                    if info["employees_a"]:
                        for name in info["employees_a"].values():
                            ui.label(f"• {name}").classes("text-sm")
                    else:
                        ui.label("Keine Zuweisung").classes("text-sm text-gray-500")

                with ui.column().classes("flex-1"):
                    ui.label("Lösung B:").classes("font-semibold text-sm")
                    if info["employees_b"]:
                        for name in info["employees_b"].values():
                            ui.label(f"• {name}").classes("text-sm")
                    else:
                        ui.label("Keine Zuweisung").classes("text-sm text-gray-500")
        else:
            ui.label("Keine Änderungen in dieser Schicht").classes("text-gray-500")

        ui.button("Schließen", on_click=dialog.close).classes("mt-4")

    dialog.open()
