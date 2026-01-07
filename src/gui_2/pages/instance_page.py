from pathlib import Path
from typing import Any, Dict, List

from nicegui import ui

from ...inputTypes.instace import Instance
from ...parseData import parseTXT
from .. import state

# Constants
DATA_DIR = (
    Path(__file__).resolve().parent.parent.parent.parent / "data" / "instance_raw"
)


# Helper Functions
def load_available_instances() -> list[str]:
    """Lädt alle verfügbaren Instance-Dateien aus dem DATA_DIR.

    Returns:
        list[str]: Sortierte Liste der Instance-Namen (mit Endung)
    """
    if not DATA_DIR.exists():
        return []

    txt_files = sorted([f.name for f in DATA_DIR.glob("*.txt")])
    return txt_files


# UI Component Functions
def render_instance_info() -> None:
    """Rendert Informationen über die aktuell geladene Instance."""
    with ui.card().classes("w-full mb-4"):
        ui.label("Aktuelle Instance").classes("text-xl font-bold mb-2")

        instance: Instance | None = state.get_instance()
        if instance is None:
            ui.label("Keine Instance geladen").classes("text-gray-500 italic")
            return

        # Grundlegende Informationen
        ui.label(f"Name: {instance.name}").classes("text-lg mb-2")
        with ui.row().classes("gap-4"):
            ui.label(f"Anzahl Tage: {instance.number_of_days}")
            ui.label(f"Anzahl Schichttypen: {len(instance.shift_types)}")
            ui.label(f"Anzahl Mitarbeiter: {len(instance.employees)}")
            ui.label(f"Wochenendtage: {len(instance.weekend_days)}")


def render_shift_type_details() -> None:
    """Rendert Details zu Schichttypen mit Dropdown."""
    instance: Instance | None = state.get_instance()
    if instance is None or not instance.shift_types:
        return

    with ui.card().classes("w-full mb-4"):
        ui.label("Schichttypen Details").classes("text-xl font-bold mb-2")

        # Dropdown für Schichttypen
        shift_type_options = {
            st.uid: f"{st.name} (Start: {st.start_time}, {st.length} min)"
            for st in instance.shift_types.values()
        }

        # Wähle standardmäßig den ersten Schichttyp
        first_shift_type_uid = next(iter(instance.shift_types.keys()))

        # Container für die Details
        detail_container = ui.column().classes("w-full mt-2")

        def show_shift_type_details(shift_type_uid: int | None) -> None:
            """Zeigt Details für den ausgewählten Schichttyp."""
            detail_container.clear()

            if shift_type_uid is None:
                return

            shift_type = instance.shift_types[shift_type_uid]

            with detail_container:
                ui.label(f"Schichttyp: {shift_type.name}").classes(
                    "text-lg font-semibold mb-2"
                )

                with ui.grid(columns=2).classes("gap-2"):
                    ui.label("UID:").classes("font-semibold")
                    ui.label(f"...{str(shift_type.uid)[-6:]}")

                    ui.label("Startzeit:").classes("font-semibold")
                    ui.label(str(shift_type.start_time))

                    ui.label("Länge:").classes("font-semibold")
                    ui.label(
                        f"{shift_type.length} Minuten ({shift_type.length / 60:.1f} Stunden)"
                    )

                    ui.label("Blockierte Schichten danach:").classes("font-semibold")
                    if shift_type.blocked_shifts_after:
                        blocked_names = [
                            instance.shift_types[uid].name
                            for uid in shift_type.blocked_shifts_after
                            if uid in instance.shift_types
                        ]
                        ui.label(", ".join(blocked_names) if blocked_names else "Keine")
                    else:
                        ui.label("Keine")

        shift_select = ui.select(
            options=shift_type_options,
            label="Schichttyp auswählen",
            value=first_shift_type_uid,
            on_change=lambda e: show_shift_type_details(e.value),
        ).classes("w-full")

        # Zeige initial den ersten Schichttyp
        show_shift_type_details(first_shift_type_uid)


def render_employee_details() -> None:
    """Rendert Details zu Mitarbeitern mit Dropdown."""
    instance: Instance | None = state.get_instance()
    if instance is None or not instance.employees:
        return

    with ui.card().classes("w-full mb-4"):
        ui.label("Mitarbeiter Details").classes("text-xl font-bold mb-2")

        # Dropdown für Mitarbeiter
        employee_options = {emp.uid: emp.name for emp in instance.employees.values()}

        # Wähle standardmäßig den ersten Mitarbeiter
        first_employee_uid = next(iter(instance.employees.keys()))

        # Container für die Details
        detail_container = ui.column().classes("w-full mt-2")

        def show_employee_details(employee_uid: int | None) -> None:
            """Zeigt Details für den ausgewählten Mitarbeiter."""
            detail_container.clear()

            if employee_uid is None:
                return

            employee = instance.employees[employee_uid]

            with detail_container:
                ui.label(f"Mitarbeiter: {employee.name}").classes(
                    "text-lg font-semibold mb-2"
                )

                with ui.grid(columns=2).classes("gap-2"):
                    ui.label("UID:").classes("font-semibold")
                    ui.label(f"...{str(employee.uid)[-6:]}")

                    ui.label("Arbeitszeit:").classes("font-semibold")
                    min_hours = employee.min_minutes_assigned / 60
                    max_hours = employee.max_minutes_assigned / 60
                    if employee.max_minutes_assigned >= 1000000:
                        ui.label(f"Min: {min_hours:.1f}h, Max: unbegrenzt")
                    else:
                        ui.label(f"Min: {min_hours:.1f}h, Max: {max_hours:.1f}h")

                    ui.label("Konsekutive Schichten:").classes("font-semibold")
                    if employee.max_number_consecutive_shifts >= 1000000:
                        ui.label(
                            f"Min: {employee.min_number_consecutive_shifts}, Max: unbegrenzt"
                        )
                    else:
                        ui.label(
                            f"Min: {employee.min_number_consecutive_shifts}, Max: {employee.max_number_consecutive_shifts}"
                        )

                    ui.label("Min. aufeinander folgende freie Tage:").classes(
                        "font-semibold"
                    )
                    ui.label(str(employee.min_number_consecutive_days_off))

                    ui.label("Max. Wochenenden:").classes("font-semibold")
                    if employee.max_number_weekends >= 1000000:
                        ui.label("Unbegrenzt")
                    else:
                        ui.label(str(employee.max_number_weekends))

                    ui.label("Blockierte Tage:").classes("font-semibold")
                    if employee.blocked_shifts:
                        ui.label(
                            ", ".join(str(d) for d in sorted(employee.blocked_shifts))
                        )
                    else:
                        ui.label("Keine")

                # Max Schichten pro Schichttyp
                if employee.max_numbers_of_shifts:
                    ui.label("Maximale Anzahl Schichten pro Typ:").classes(
                        "font-semibold mt-3"
                    )
                    with ui.column().classes("ml-4"):
                        for (
                            type_uid,
                            max_count,
                        ) in employee.max_numbers_of_shifts.items():
                            type_name = instance.shift_types.get(type_uid, None)
                            if type_name:
                                ui.label(f"• {type_name.name}: {max_count}")

        employee_select = ui.select(
            options=employee_options,
            label="Mitarbeiter auswählen",
            value=first_employee_uid,
            on_change=lambda e: show_employee_details(e.value),
        ).classes("w-full")

        # Zeige initial den ersten Mitarbeiter
        show_employee_details(first_employee_uid)


def render_shifts_table() -> None:
    """Rendert eine Tabelle mit allen Shifts."""
    instance: Instance | None = state.get_instance()
    if instance is None or not instance.shifts:
        return

    with ui.card().classes("w-full mb-4"):
        ui.label("Schichten Übersicht").classes("text-xl font-bold mb-2")

        days = sorted(instance.shifts.keys())
        shift_types = sorted(instance.shift_types.keys())

        columns = _build_shifts_table_columns(days)
        rows, shift_cell_mapping = _build_shifts_table_rows(instance, days, shift_types)

        table = (
            ui.table(columns=columns, rows=rows, row_key="row_key")
            .classes("w-full")
            .props("flat hide-selected-banner dense")
        )

        # Custom cell rendering with clickable elements
        table.add_slot(
            "body-cell",
            """
            <q-td :props="props">
                <div v-if="props.col.name === 'shift_type'" class="text-weight-medium">
                    {{ props.value }}
                </div>
                <div v-else class="q-pa-xs cursor-pointer hover:bg-gray-100" 
                     @click="() => $parent.$emit('cell_click', props.row.row_key, props.col.name)">
                    <div class="text-xs text-gray-600">{{ props.value }}</div>
                </div>
            </q-td>
        """,
        )

        table.on(
            "cell_click",
            lambda e: _display_shift_details_dialog(
                e.args[0], e.args[1], instance, shift_cell_mapping
            ),
        )


def _build_shifts_table_columns(days: List[int]) -> List[Dict[str, str]]:
    """Build table column definitions for shifts."""
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
                "align": "center",
            }
        )

    return columns


def _build_shifts_table_rows(
    instance: Instance, days: List[int], shift_types: List[Any]
) -> tuple[List[Dict[str, Any]], Dict[str, tuple[int, int]]]:
    """Build table row data for shifts."""
    shift_cell_mapping = {}
    rows = []

    for idx, shift_type_uid in enumerate(shift_types):
        row_key = f"shift_{idx}"
        shift_type = instance.shift_types[shift_type_uid]

        row = {
            "shift_type": shift_type.name,
            "row_key": row_key,
        }

        for day in days:
            shift = instance.shifts.get(day, {}).get(shift_type_uid)
            if shift:
                cell_key = f"{row_key}_day_{day}"
                shift_cell_mapping[cell_key] = (day, shift_type_uid)

                # Show preferred employee count as summary
                if shift.preffert_number_employees > 0:
                    row[f"day_{day}"] = f"👥 {shift.preffert_number_employees}"
                else:
                    row[f"day_{day}"] = "—"
            else:
                row[f"day_{day}"] = "—"

        rows.append(row)

    return rows, shift_cell_mapping


def _display_shift_details_dialog(
    row_key: str,
    col_name: str,
    instance: Instance,
    shift_cell_mapping: Dict[str, tuple[int, int]],
) -> None:
    """Display detailed information about a shift in a dialog."""
    if col_name == "shift_type":
        return

    cell_key = f"{row_key}_{col_name}"
    if cell_key not in shift_cell_mapping:
        return

    day, shift_type_uid = shift_cell_mapping[cell_key]
    shift = instance.shifts[day][shift_type_uid]
    shift_type = instance.shift_types[shift_type_uid]

    with ui.dialog() as dialog, ui.card().classes("min-w-[600px]"):
        ui.label(f"Schicht Details: Tag {day}, {shift_type.name}").classes(
            "text-xl font-bold mb-4"
        )

        # Basic Information
        with ui.card().classes("w-full mb-3 bg-gray-50"):
            ui.label("Grundinformationen").classes("font-semibold mb-2")
            with ui.grid(columns=2).classes("gap-2"):
                ui.label("Schicht UID:").classes("font-semibold")
                ui.label(f"...{str(shift.uid)[-6:]}")

                ui.label("Schichttyp UID:").classes("font-semibold")
                ui.label(f"...{str(shift_type_uid)[-6:]}")

                ui.label("Wochenende:").classes("font-semibold")
                ui.label("Ja" if shift.is_weekend else "Nein")

                ui.label("Startzeit:").classes("font-semibold")
                ui.label(str(shift_type.start_time))

                ui.label("Länge:").classes("font-semibold")
                ui.label(f"{shift_type.length} min ({shift_type.length / 60:.1f}h)")

        # Coverage Requirements
        with ui.card().classes("w-full mb-3 bg-blue-50"):
            ui.label("Besetzungsanforderungen").classes("font-semibold mb-2")
            with ui.grid(columns=2).classes("gap-2"):
                ui.label("Bevorzugte Anzahl:").classes("font-semibold")
                ui.label(str(shift.preffert_number_employees))

                ui.label("Gewicht Unterbesetzung:").classes("font-semibold")
                ui.label(str(shift.weight_below_preferred))

                ui.label("Gewicht Überbesetzung:").classes("font-semibold")
                ui.label(str(shift.weight_above_preferred))

        # Employee Assignments/Bans
        if shift.assign_employee_day_shift or shift.ban_employee_day_shift:
            with ui.card().classes("w-full mb-3 bg-green-50"):
                ui.label("Mitarbeiter Zuweisungen").classes("font-semibold mb-2")

                if shift.assign_employee_day_shift:
                    ui.label("Zugewiesene Mitarbeiter:").classes(
                        "text-sm font-semibold mt-2"
                    )
                    for emp_uid in shift.assign_employee_day_shift:
                        emp = instance.employees.get(emp_uid)
                        if emp:
                            ui.label(f"• {emp.name} (...{str(emp_uid)[-6:]})")

                if shift.ban_employee_day_shift:
                    ui.label("Gesperrte Mitarbeiter:").classes(
                        "text-sm font-semibold mt-2"
                    )
                    for emp_uid in shift.ban_employee_day_shift:
                        emp = instance.employees.get(emp_uid)
                        if emp:
                            ui.label(f"• {emp.name} (...{str(emp_uid)[-6:]})")

        # Penalty Information
        if (
            shift.penalty_assigned_day_employee
            or shift.penalty_not_assigned_day_employee
        ):
            with ui.card().classes("w-full mb-3 bg-yellow-50"):
                ui.label("Strafpunkte").classes("font-semibold mb-2")

                if shift.penalty_assigned_day_employee:
                    ui.label("Strafpunkte bei Zuweisung:").classes(
                        "text-sm font-semibold mt-2"
                    )
                    for emp_uid, penalty in shift.penalty_assigned_day_employee.items():
                        if penalty > 0:
                            emp = instance.employees.get(emp_uid)
                            if emp:
                                ui.label(
                                    f"• {emp.name} (...{str(emp_uid)[-6:]}): {penalty}"
                                )

                if shift.penalty_not_assigned_day_employee:
                    ui.label("Strafpunkte bei Nicht-Zuweisung:").classes(
                        "text-sm font-semibold mt-2"
                    )
                    for (
                        emp_uid,
                        penalty,
                    ) in shift.penalty_not_assigned_day_employee.items():
                        if penalty > 0:
                            emp = instance.employees.get(emp_uid)
                            if emp:
                                ui.label(
                                    f"• {emp.name} (...{str(emp_uid)[-6:]}): {penalty}"
                                )

        ui.button("Schließen", on_click=dialog.close).classes("mt-4")

    dialog.open()


# Main Page Function
def instance_page():
    """Seite für Instance-Verwaltung und -Laden."""

    def load_instance(instance_name: str) -> None:
        """Lädt eine Instance und aktualisiert den globalen State.

        Args:
            instance_name: Name der zu ladenden Instance-Datei
        """
        try:
            instance_path = DATA_DIR / instance_name
            loaded_instance = parseTXT.parse_txt(instance_path)

            # Setze Instance im globalen State
            state.set_instance(loaded_instance)
            state.set_solution(None)  # Lösung zurücksetzen

            update_instance_display()
            ui.notify(
                f"Instance '{instance_name}' erfolgreich geladen", type="positive"
            )
        except Exception as e:
            ui.notify(f"Fehler beim Laden: {str(e)}", type="negative")

    def update_instance_display() -> None:
        """Aktualisiert die Anzeige der Instance-Details."""
        instance_container.clear()

        with instance_container:
            render_instance_info()
            render_shift_type_details()
            render_employee_details()
            render_shifts_table()

    # UI Layout
    with ui.card().classes("w-full mb-4"):
        ui.label("Instance Manager").classes("text-2xl font-bold mb-4")

        # Instance-Auswahl
        available_instances = load_available_instances()

        if not available_instances:
            ui.label("Keine Instances gefunden").classes("text-orange-500")
            ui.label(f"Pfad: {DATA_DIR}").classes("text-sm text-gray-500")
        else:
            ui.label(f"{len(available_instances)} Instances verfügbar").classes(
                "text-sm text-gray-600 mb-2"
            )

            with ui.row().classes("w-full gap-4 items-center"):
                instance_select = ui.select(
                    options=available_instances,
                    label="Instance auswählen",
                    on_change=lambda e: load_instance(e.value) if e.value else None,
                ).classes("flex-grow")

                ui.button(
                    "Neu laden",
                    icon="refresh",
                    on_click=lambda: [
                        instance_select.set_options(load_available_instances()),
                        ui.notify("Instances aktualisiert", type="info"),
                    ],
                ).props("flat")

    # Container für die Instance-Anzeige
    instance_container = ui.column().classes("w-full")

    # Zeige aktuelle Instance beim Laden der Seite
    if state.get_instance() is not None:
        update_instance_display()
