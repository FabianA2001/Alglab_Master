from datetime import time
from pathlib import Path
from typing import Any, Dict, List

from nicegui import ui

from ...help_functions import hash_string
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


def render_shift_type_details(refresh_callback=None) -> None:
    """Rendert Details zu Schichttypen mit Dropdown.

    Args:
        refresh_callback: Optional callback function to refresh the display after changes
    """
    instance: Instance | None = state.get_instance()
    if instance is None:
        return

    with ui.card().classes("w-full mb-4"):
        with ui.row().classes("w-full items-center justify-between mb-2"):
            ui.label("Schichttypen Details").classes("text-xl font-bold")
            ui.button(
                "Neuer Schichttyp",
                icon="add",
                on_click=lambda: _show_add_shift_type_dialog(
                    instance, refresh_callback
                ),
            ).props("color=primary")

        if not instance.shift_types:
            ui.label("Keine Schichttypen vorhanden").classes(
                "text-gray-500 italic mt-2"
            )
            return

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

            shift_type = instance.shift_types.get(shift_type_uid)
            if shift_type is None:
                return

            with detail_container:
                with ui.row().classes("w-full items-center justify-between mb-2"):
                    ui.label(f"Schichttyp: {shift_type.name}").classes(
                        "text-lg font-semibold"
                    )
                    ui.button(
                        "Bearbeiten",
                        icon="edit",
                        on_click=lambda uid=shift_type_uid: _show_edit_shift_type_dialog(
                            instance,
                            uid,  # type: ignore
                            refresh_callback,
                        ),
                    ).props("flat dense color=primary")

                with ui.grid(columns=2).classes("gap-2"):
                    ui.label("UID:").classes("font-semibold")
                    ui.label(f"...{str(shift_type.uid)[-6:]}")

                    ui.label("Startzeit:").classes("font-semibold")
                    ui.label(str(shift_type.start_time))

                    ui.label("Länge:").classes("font-semibold")

                    ui.label("Blockierte Schichten danach:").classes("font-semibold")
                    if shift_type.blocked_shifts_after:
                        blocked_names = [
                            instance.shift_types.get(uid).name
                            for uid in shift_type.blocked_shifts_after
                            if instance.shift_types.get(uid) is not None
                        ]
                        ui.label(", ".join(blocked_names) if blocked_names else "Keine")
                    else:
                        ui.label("Keine")

        ui.select(
            options=shift_type_options,
            label="Schichttyp auswählen",
            value=first_shift_type_uid,
            on_change=lambda e: show_shift_type_details(e.value),
        ).classes("w-full")

        # Zeige initial den ersten Schichttyp
        show_shift_type_details(first_shift_type_uid)


def render_employee_details(refresh_callback=None) -> None:
    """Rendert Details zu Mitarbeitern mit Dropdown.

    Args:
        refresh_callback: Optional callback function to refresh the display after changes
    """
    instance: Instance | None = state.get_instance()
    if instance is None:
        return

    with ui.card().classes("w-full mb-4"):
        with ui.row().classes("w-full items-center justify-between mb-2"):
            ui.label("Mitarbeiter Details").classes("text-xl font-bold")
            ui.button(
                "Neuer Mitarbeiter",
                icon="add",
                on_click=lambda: _show_add_employee_dialog(instance, refresh_callback),
            ).props("color=primary")

        if not instance.employees:
            ui.label("Keine Mitarbeiter vorhanden").classes("text-gray-500 italic mt-2")
            return

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

            employee = instance.employees.get(employee_uid)
            if employee is None:
                return

            with detail_container:
                with ui.row().classes("w-full items-center justify-between mb-2"):
                    ui.label(f"Mitarbeiter: {employee.name}").classes(
                        "text-lg font-semibold"
                    )
                    ui.button(
                        "Bearbeiten",
                        icon="edit",
                        on_click=lambda _: _show_edit_employee_dialog(
                            instance, employee_uid, refresh_callback
                        ),
                    ).props("flat dense color=primary")

                with ui.grid(columns=2).classes("gap-2"):
                    ui.label("UID:").classes("font-semibold")
                    ui.label(f"...{str(employee.uid)[-6:]}")

                    ui.label("Arbeitszeit:").classes("font-semibold")
                    min_hours = employee.min_minutes_assigned / 60
                    max_hours = employee.max_minutes_assigned / 60
                    ui.label(f"Min: {min_hours:.1f}h, Max: {max_hours:.1f}h")

                    ui.label("Konsekutive Schichten:").classes("font-semibold")
                    ui.label(
                        f"Min: {employee.min_number_consecutive_shifts}, Max: {employee.max_number_consecutive_shifts}"
                    )

                    ui.label("Min. aufeinander folgende freie Tage:").classes(
                        "font-semibold"
                    )
                    ui.label(str(employee.min_number_consecutive_days_off))

                    ui.label("Max. Wochenenden:").classes("font-semibold")
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

        ui.select(
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

        all_days = sorted(instance.shifts.keys())
        shift_types = sorted(instance.shift_types.keys())

        # Calculate weeks (7 days per week)
        num_weeks = (len(all_days) + 6) // 7  # Round up
        weeks = []
        for week_idx in range(num_weeks):
            start_idx = week_idx * 7
            end_idx = min(start_idx + 7, len(all_days))
            week_days = all_days[start_idx:end_idx]
            weeks.append((week_idx + 1, week_days))

        # State for current week
        current_week = {"value": 0}  # Index in weeks list

        @ui.refreshable
        def render_table():
            """Render the table for the current week."""
            week_num, days = weeks[current_week["value"]]

            ui.label(f"Woche {week_num} (Tage {days[0]} - {days[-1]})").classes(
                "text-lg font-semibold mb-2"
            )

            columns = _build_shifts_table_columns(days)
            rows, shift_cell_mapping = _build_shifts_table_rows(
                instance, days, shift_types
            )

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

        # Week navigation
        if num_weeks > 1:
            with ui.row().classes("gap-2 items-center mb-4"):
                ui.button(
                    icon="chevron_left",
                    on_click=lambda: [
                        current_week.update(value=max(0, current_week["value"] - 1)),
                        render_table.refresh(),
                    ],
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
                    on_click=lambda: [
                        current_week.update(
                            value=min(num_weeks - 1, current_week["value"] + 1)
                        ),
                        render_table.refresh(),
                    ],
                ).props("flat").bind_enabled_from(
                    current_week, "value", lambda v: v < num_weeks - 1
                )

        # Render table
        render_table()


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
        shift_type = instance.shift_types.get(shift_type_uid)
        if not shift_type:
            continue

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


def _show_employee_dialog(
    instance: Instance, refresh_callback=None, employee_uid: int | None = None
) -> None:
    """Zeigt einen Dialog zum Hinzufügen oder Bearbeiten eines Mitarbeiters.

    Args:
        instance: Die aktuelle Instance
        refresh_callback: Optional callback function to refresh the display
        employee_uid: Optional UID des zu bearbeitenden Mitarbeiters (None = neuer Mitarbeiter)
    """
    from ...inputTypes.employee import Employee

    # Bei Bearbeitung: Lade bestehenden Mitarbeiter
    is_edit = employee_uid is not None

    if is_edit:
        employee = instance.employees.get(employee_uid)
        if not employee:
            ui.notify("Mitarbeiter nicht gefunden", type="negative")
            return
    else:
        employee = None

    # Default Werte (neu) oder vorausgefüllte Werte (bearbeiten)
    form_data = {
        "name": employee.name if employee else "",
        "min_minutes_assigned": employee.min_minutes_assigned if employee else 0,
        "max_minutes_assigned": employee.max_minutes_assigned if employee else 999999,
        "min_number_consecutive_shifts": employee.min_number_consecutive_shifts
        if employee
        else 0,
        "max_number_consecutive_shifts": employee.max_number_consecutive_shifts
        if employee
        else 999999,
        "min_number_consecutive_days_off": employee.min_number_consecutive_days_off
        if employee
        else 1,
        "max_number_weekends": employee.max_number_weekends if employee else 999999,
        "blocked_shifts": (
            employee.blocked_shifts.copy() if employee.blocked_shifts else set()
        )
        if employee
        else set(),
        "max_numbers_of_shifts": (
            employee.max_numbers_of_shifts.copy()
            if employee.max_numbers_of_shifts
            else {}
        )
        if employee
        else {},
    }

    def save_employee():
        """Fügt den neuen Mitarbeiter hinzu oder aktualisiert einen bestehenden."""
        try:
            # Validierung
            if not form_data["name"] or not form_data["name"].strip():
                ui.notify("Bitte geben Sie einen Namen ein", type="warning")
                return

            # Prüfe ob Name bereits existiert (bei Edit: außer bei gleichem Employee)
            if any(
                emp.name.lower() == form_data["name"].strip().lower()
                and uid != employee_uid
                for uid, emp in instance.employees.items()
            ):
                ui.notify(
                    f"Ein Mitarbeiter mit dem Namen '{form_data['name']}' existiert bereits",
                    type="warning",
                )
                return

            # Validiere Wertebereiche
            if form_data["min_minutes_assigned"] < 0:
                ui.notify(
                    "Minimale Arbeitszeit kann nicht negativ sein", type="warning"
                )
                return

            if form_data["max_minutes_assigned"] < form_data["min_minutes_assigned"]:
                ui.notify(
                    "Maximale Arbeitszeit muss >= minimale Arbeitszeit sein",
                    type="warning",
                )
                return

            if (
                form_data["max_number_consecutive_shifts"]
                < form_data["min_number_consecutive_shifts"]
            ):
                ui.notify(
                    "Maximale konsekutive Schichten muss >= minimale sein",
                    type="warning",
                )
                return

            if is_edit:
                # Aktualisiere bestehenden Mitarbeiter
                if employee:  # Type guard
                    employee.name = form_data["name"].strip()
                    employee.min_minutes_assigned = form_data["min_minutes_assigned"]
                    employee.max_minutes_assigned = form_data["max_minutes_assigned"]
                    employee.min_number_consecutive_shifts = form_data[
                        "min_number_consecutive_shifts"
                    ]
                    employee.max_number_consecutive_shifts = form_data[
                        "max_number_consecutive_shifts"
                    ]
                    employee.min_number_consecutive_days_off = form_data[
                        "min_number_consecutive_days_off"
                    ]
                    employee.max_number_weekends = form_data["max_number_weekends"]
                    employee.blocked_shifts = (
                        form_data["blocked_shifts"].copy()
                        if form_data["blocked_shifts"]
                        else set()
                    )
                    employee.max_numbers_of_shifts = (
                        form_data["max_numbers_of_shifts"].copy()
                        if form_data["max_numbers_of_shifts"]
                        else {}
                    )

                success_msg = (
                    f"Mitarbeiter '{form_data['name']}' erfolgreich aktualisiert"
                )
            else:
                # Erstelle neuen Mitarbeiter
                new_uid = hash_string(f"employee_{form_data['name'].strip()}")

                new_employee = Employee(
                    uid=new_uid,
                    name=form_data["name"].strip(),
                    min_minutes_assigned=form_data["min_minutes_assigned"],
                    max_minutes_assigned=form_data["max_minutes_assigned"],
                    min_number_consecutive_shifts=form_data[
                        "min_number_consecutive_shifts"
                    ],
                    max_number_consecutive_shifts=form_data[
                        "max_number_consecutive_shifts"
                    ],
                    min_number_consecutive_days_off=form_data[
                        "min_number_consecutive_days_off"
                    ],
                    max_number_weekends=form_data["max_number_weekends"],
                    blocked_shifts=form_data["blocked_shifts"].copy()
                    if form_data["blocked_shifts"]
                    else set(),
                    max_numbers_of_shifts=form_data["max_numbers_of_shifts"].copy()
                    if form_data["max_numbers_of_shifts"]
                    else {},
                )

                instance.employees[new_uid] = new_employee
                success_msg = (
                    f"Mitarbeiter '{form_data['name']}' erfolgreich hinzugefügt"
                )

            # Speichere geänderte Instance
            state.clear_solutions()
            state.set_instance(instance)

            ui.notify(success_msg, type="positive")

            # Aktualisiere Anzeige
            if refresh_callback:
                refresh_callback()

            dialog.close()

        except Exception as e:
            ui.notify(
                f"Fehler beim {'Aktualisieren' if is_edit else 'Hinzufügen'}: {str(e)}",
                type="negative",
            )

    dialog_title = (
        f"Mitarbeiter bearbeiten: {employee.name}"
        if (is_edit and employee)
        else "Neuen Mitarbeiter hinzufügen"
    )
    button_text = "Speichern" if is_edit else "Hinzufügen"

    with ui.dialog() as dialog, ui.card().classes("min-w-[600px]"):
        ui.label(dialog_title).classes("text-xl font-bold mb-4")

        with ui.column().classes("w-full gap-3"):
            # Name
            ui.input(label="Name", placeholder="z.B. Max Mustermann").classes(
                "w-full"
            ).bind_value(form_data, "name")

            ui.separator()

            # Arbeitszeit
            ui.label("Arbeitszeit (in Minuten)").classes("font-semibold")

            ui.number(label="Minimale Arbeitszeit", min=0, format="%d").classes(
                "w-full"
            ).bind_value(form_data, "min_minutes_assigned")

            ui.number(label="Maximale Arbeitszeit", min=0, format="%d").classes(
                "w-full"
            ).bind_value(form_data, "max_minutes_assigned")

            # Konsekutive Schichten
            ui.label("Konsekutive Schichten").classes("font-semibold")
            ui.number(label="Minimale Anzahl", min=0, format="%d").classes(
                "w-full"
            ).bind_value(form_data, "min_number_consecutive_shifts")

            ui.number(label="Maximale Anzahl", min=0, format="%d").classes(
                "w-full"
            ).bind_value(form_data, "max_number_consecutive_shifts")

            # Weitere Parameter
            ui.label("Weitere Einstellungen").classes("font-semibold")

            ui.number(
                label="Min. aufeinander folgende freie Tage", min=0, format="%d"
            ).classes("w-full").bind_value(form_data, "min_number_consecutive_days_off")

            ui.number(label="Max. Wochenenden", min=0, format="%d").classes(
                "w-full"
            ).bind_value(form_data, "max_number_weekends")

            # Blockierte Tage
            ui.label("Blockierte Tage (optional)").classes("font-semibold")
            ui.label(
                f"Geben Sie Tage ein, an denen der Mitarbeiter nicht arbeiten kann (0 bis {instance.number_of_days - 1})"
            ).classes("text-sm text-gray-600 mb-2")

            # Vorausgefüllte blockierte Tage (bei Edit)
            initial_blocked = (
                ",".join(str(d) for d in sorted(form_data["blocked_shifts"]))
                if form_data["blocked_shifts"]
                else ""
            )

            blocked_days_input = ui.input(
                label="Blockierte Tage (kommagetrennt)",
                placeholder="z.B. 0,5,10,15",
                value=initial_blocked,
            ).classes("w-full")

            blocked_days_display = ui.label("").classes("text-sm text-gray-600 mt-1")

            def update_blocked_days():
                """Parst und validiert die blockierten Tage."""
                input_value = blocked_days_input.value or ""
                if not input_value.strip():
                    form_data["blocked_shifts"] = set()
                    blocked_days_display.text = ""
                    return

                try:
                    days = [int(d.strip()) for d in input_value.split(",") if d.strip()]
                    invalid_days = [
                        d for d in days if d < 0 or d > instance.number_of_days - 1
                    ]

                    if invalid_days:
                        blocked_days_display.text = (
                            f"⚠️ Ungültige Tage: {', '.join(map(str, invalid_days))}"
                        )
                        blocked_days_display.classes(
                            "text-sm text-orange-600 mt-1",
                            remove="text-gray-600 text-green-600",
                        )
                        return

                    form_data["blocked_shifts"] = set(days)
                    if days:
                        blocked_days_display.text = (
                            f"✓ {len(days)} Tag(e) blockiert: {sorted(days)}"
                        )
                        blocked_days_display.classes(
                            "text-sm text-green-600 mt-1",
                            remove="text-gray-600 text-orange-600",
                        )
                    else:
                        blocked_days_display.text = ""

                except ValueError:
                    blocked_days_display.text = (
                        "⚠️ Bitte nur Zahlen eingeben (kommagetrennt)"
                    )
                    blocked_days_display.classes(
                        "text-sm text-orange-600 mt-1",
                        remove="text-gray-600 text-green-600",
                    )

            blocked_days_input.on("blur", update_blocked_days)

            # Initial validation (bei Edit)
            if initial_blocked:
                update_blocked_days()

            ui.separator()

            # Maximale Anzahl Schichten pro Schichttyp
            if instance.shift_types:
                ui.label("Maximale Anzahl Schichten pro Schichttyp (optional)").classes(
                    "font-semibold"
                )
                ui.label(
                    "Wählen Sie einen Schichttyp aus und geben Sie die maximale Anzahl an (leer = unbegrenzt)"
                ).classes("text-sm text-gray-600 mb-2")

                shift_type_limits = form_data["max_numbers_of_shifts"].copy()
                shift_type_options = {
                    uid: st.name for uid, st in instance.shift_types.items()
                }
                current_shift_type_uid = next(iter(instance.shift_types.keys()))

                def update_count_field(shift_type_uid):
                    if shift_type_uid in shift_type_limits:
                        count_input.value = shift_type_limits[shift_type_uid]
                    else:
                        count_input.set_value(None)

                def save_current_value():
                    value = count_input.value
                    if value is not None and value > 0:
                        shift_type_limits[current_shift_type_uid] = int(value)
                    elif current_shift_type_uid in shift_type_limits:
                        del shift_type_limits[current_shift_type_uid]
                    form_data["max_numbers_of_shifts"] = shift_type_limits.copy()

                def on_shift_type_change(e):
                    nonlocal current_shift_type_uid
                    save_current_value()
                    current_shift_type_uid = e.value
                    update_count_field(current_shift_type_uid)

                def reset_current_value():
                    if current_shift_type_uid in shift_type_limits:
                        del shift_type_limits[current_shift_type_uid]
                    form_data["max_numbers_of_shifts"] = shift_type_limits.copy()
                    count_input.set_value(None)
                    ui.notify("Limit entfernt (unbegrenzt)", type="info")

                with ui.row().classes("w-full items-center gap-2"):
                    ui.select(
                        options=shift_type_options,
                        label="Schichttyp",
                        value=current_shift_type_uid,
                        on_change=on_shift_type_change,
                    ).classes("flex-grow")

                    count_input = ui.number(
                        label="Max. Anzahl",
                        min=1,
                        format="%d",
                        placeholder="unbegrenzt",
                        on_change=lambda: save_current_value(),
                    ).classes("w-48")

                    ui.button(icon="clear", on_click=reset_current_value).props(
                        "flat"
                    ).tooltip("Auf unbegrenzt zurücksetzen")

                update_count_field(current_shift_type_uid)

            # Info Box (nur bei Edit)
            if is_edit:
                with ui.card().classes("w-full bg-yellow-50 mt-2"):
                    ui.label("⚠️ Wichtig").classes("font-semibold")
                    ui.label("• Die UID des Mitarbeiters bleibt unverändert").classes(
                        "text-sm"
                    )

        # Buttons
        with ui.row().classes("w-full justify-end gap-2 mt-4"):
            ui.button("Abbrechen", on_click=dialog.close).props("flat")
            ui.button(button_text, on_click=save_employee).props("color=primary")

    dialog.open()


def _show_add_employee_dialog(instance: Instance, refresh_callback=None) -> None:
    """Zeigt einen Dialog zum Hinzufügen eines neuen Mitarbeiters."""
    _show_employee_dialog(instance, refresh_callback, employee_uid=None)


def _show_edit_employee_dialog(
    instance: Instance, employee_uid: int, refresh_callback=None
) -> None:
    """Zeigt einen Dialog zum Bearbeiten eines bestehenden Mitarbeiters."""
    _show_employee_dialog(instance, refresh_callback, employee_uid=employee_uid)


def _show_shift_type_dialog(
    instance: Instance, refresh_callback=None, shift_type_uid: int | None = None
) -> None:
    """Zeigt einen Dialog zum Hinzufügen oder Bearbeiten eines Schichttyps.

    Args:
        instance: Die aktuelle Instance
        refresh_callback: Optional callback function to refresh the display
        shift_type_uid: Optional UID des zu bearbeitenden Schichttyps (None = neuer Typ)
    """
    from ...inputTypes.shiftType import ShiftType

    # Bei Bearbeitung: Lade bestehenden Schichttyp
    is_edit = shift_type_uid is not None
    shift_type = None

    if is_edit:
        shift_type = instance.shift_types.get(shift_type_uid)
        if not shift_type:
            ui.notify("Schichttyp nicht gefunden", type="negative")
            return

    # Default Werte (neu) oder vorausgefüllte Werte (bearbeiten)
    form_data = {
        "name": shift_type.name if (is_edit and shift_type) else "",
        "start_time": shift_type.start_time.strftime("%H:%M")
        if (is_edit and shift_type)
        else "00:00",
        "length": shift_type.length
        if (is_edit and shift_type)
        else 480,  # 8 Stunden in Minuten
        "blocked_shifts_after": (
            shift_type.blocked_shifts_after.copy()
            if shift_type.blocked_shifts_after
            else set()
        )
        if (is_edit and shift_type)
        else set(),
    }

    # Optionen für blockierte Schichten (ohne den aktuellen Typ bei Edit)
    shift_type_options = {
        uid: f"{st.name} ({st.start_time})"
        for uid, st in instance.shift_types.items()
        if not is_edit or uid != shift_type_uid
    }

    def save_shift_type():
        """Fügt den neuen Schichttyp hinzu oder aktualisiert einen bestehenden."""
        try:
            # Validierung
            if not form_data["name"] or not form_data["name"].strip():
                ui.notify("Bitte geben Sie einen Namen ein", type="warning")
                return

            if form_data["length"] <= 0:
                ui.notify("Die Länge muss größer als 0 sein", type="warning")
                return

            try:
                hours, minutes = map(int, form_data["start_time"].split(":"))
            except ValueError:
                ui.notify("Die Startzeit muss im Format HH:MM sein", type="warning")
                return

            if not (0 <= hours < 24 and 0 <= minutes < 60):
                ui.notify(
                    "Die Startzeit muss eine gültige Uhrzeit sein", type="warning"
                )
                return

            if is_edit:
                # Prüfe ob Name bereits existiert (außer bei gleichem Typ)
                if any(
                    st.name.lower() == form_data["name"].strip().lower()
                    and uid != shift_type_uid
                    for uid, st in instance.shift_types.items()
                ):
                    ui.notify(
                        f"Ein anderer Schichttyp mit dem Namen '{form_data['name']}' existiert bereits",
                        type="warning",
                    )
                    return

                # Aktualisiere den Schichttyp
                if shift_type:  # Type guard
                    shift_type.name = form_data["name"].strip()
                    shift_type.start_time = time(hour=hours, minute=minutes)
                    shift_type.length = form_data["length"]
                    shift_type.blocked_shifts_after = (
                        form_data["blocked_shifts_after"].copy()
                        if form_data["blocked_shifts_after"]
                        else set()
                    )

                success_msg = (
                    f"Schichttyp '{form_data['name']}' erfolgreich aktualisiert"
                )
            else:
                # Prüfe ob Name bereits existiert
                if any(
                    st.name.lower() == form_data["name"].strip().lower()
                    for st in instance.shift_types.values()
                ):
                    ui.notify(
                        f"Ein Schichttyp mit dem Namen '{form_data['name']}' existiert bereits",
                        type="warning",
                    )
                    return

                # Generiere neue eindeutige UID basierend auf dem Namen
                new_uid = hash_string(f"shift_type_{form_data['name'].strip()}")

                # Erstelle neuen Schichttyp
                new_shift_type = ShiftType(
                    uid=new_uid,
                    name=form_data["name"].strip(),
                    start_time=time(hour=hours, minute=minutes),
                    length=form_data["length"],
                    blocked_shifts_after=form_data["blocked_shifts_after"].copy()
                    if form_data["blocked_shifts_after"]
                    else set(),
                )

                # Füge Schichttyp zur Instance hinzu
                instance.shift_types[new_uid] = new_shift_type

                # Erstelle Default-Shifts für alle Tage
                from ...inputTypes.shift import Shift

                for day in range(1, instance.number_of_days + 1):
                    # Prüfe ob Tag bereits existiert
                    if day not in instance.shifts:
                        instance.shifts[day] = {}

                    # Prüfe ob Shift für diesen Tag und Typ bereits existiert
                    day_shifts = instance.shifts.get(day, {})
                    if new_uid not in day_shifts:
                        # Bestimme ob Wochenende
                        is_weekend = day in instance.weekend_days

                        # Generiere Shift UID
                        shift_uid = hash_string(f"shift_{day}_{new_uid}")

                        # Erstelle neue Default-Shift
                        new_shift = Shift(
                            uid=shift_uid,
                            preffert_number_employees=1,
                            weight_below_preferred=1,
                            weight_above_preferred=1,
                            is_weekend=is_weekend,
                            assign_employee_day_shift=set(),
                            ban_employee_day_shift=set(),
                            penalty_assigned_day_employee={},
                            penalty_not_assigned_day_employee={},
                        )

                        instance.shifts[day][new_uid] = new_shift

                success_msg = (
                    f"Schichttyp '{form_data['name']}' erfolgreich hinzugefügt"
                )

            # Speichere geänderte Instance
            state.clear_solutions()
            state.set_instance(instance)

            ui.notify(success_msg, type="positive")

            # Aktualisiere Anzeige
            if refresh_callback:
                refresh_callback()

            dialog.close()

        except Exception as e:
            ui.notify(
                f"Fehler beim {'Aktualisieren' if is_edit else 'Hinzufügen'}: {str(e)}",
                type="negative",
            )

    dialog_title = (
        f"Schichttyp bearbeiten: {shift_type.name}"
        if (is_edit and shift_type)
        else "Neuen Schichttyp hinzufügen"
    )
    button_text = "Speichern" if is_edit else "Hinzufügen"

    with ui.dialog() as dialog, ui.card().classes("min-w-[500px]"):
        ui.label(dialog_title).classes("text-xl font-bold mb-4")

        with ui.column().classes("w-full gap-3"):
            # Name
            ui.input(
                label="Name", placeholder="z.B. Frühschicht, Spätschicht, Nachtschicht"
            ).classes("w-full").bind_value(form_data, "name")

            # Startzeit
            ui.input(label="Startzeit (HH:MM)", placeholder="08:00").classes(
                "w-full"
            ).bind_value(form_data, "start_time")
            # Länge in Minuten (mit Live-Update für Edit, ohne für Add da es dort schon ist)
            if not is_edit:
                length_label = ui.label("").classes("text-sm text-gray-600")

                def update_length_label():
                    hours = form_data["length"] / 60
                    length_label.text = f"= {hours:.1f} Stunden"

                ui.number(label="Länge in Minuten", min=1, format="%d").classes(
                    "w-full"
                ).bind_value(form_data, "length").on_value_change(
                    lambda: update_length_label()
                )

                update_length_label()
            else:
                ui.number(label="Länge in Minuten", min=1, format="%d").classes(
                    "w-full"
                ).bind_value(form_data, "length")

            ui.separator()

            # Blockierte Schichten danach
            if shift_type_options:
                ui.label("Blockierte Schichttypen danach (optional)").classes(
                    "font-semibold"
                )
                ui.label(
                    "Wählen Sie Schichttypen aus, die nach diesem Schichttyp nicht erlaubt sind"
                ).classes("text-sm text-gray-600 mb-2")

                ui.select(
                    options=shift_type_options,
                    multiple=True,
                    label="Blockierte Schichttypen",
                ).classes("w-full").bind_value(form_data, "blocked_shifts_after")

            # Info Box (nur bei Edit)
            if is_edit:
                with ui.card().classes("w-full bg-yellow-50 mt-2"):
                    ui.label("⚠️ Wichtig").classes("font-semibold")
                    ui.label(
                        "• Änderungen am Namen oder der Länge betreffen bestehende Schichten"
                    ).classes("text-sm")
                    ui.label("• Die UID des Schichttyps bleibt unverändert").classes(
                        "text-sm"
                    )

        # Buttons
        with ui.row().classes("w-full justify-end gap-2 mt-4"):
            ui.button("Abbrechen", on_click=dialog.close).props("flat")
            ui.button(button_text, on_click=save_shift_type).props("color=primary")

    dialog.open()


def _show_add_shift_type_dialog(instance: Instance, refresh_callback=None) -> None:
    """Zeigt einen Dialog zum Hinzufügen eines neuen Schichttyps."""
    _show_shift_type_dialog(instance, refresh_callback, shift_type_uid=None)


def _show_edit_shift_type_dialog(
    instance: Instance, shift_type_uid: int, refresh_callback=None
) -> None:
    """Zeigt einen Dialog zum Bearbeiten eines bestehenden Schichttyps."""
    _show_shift_type_dialog(instance, refresh_callback, shift_type_uid=shift_type_uid)


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
    shift = instance.shifts.get(day, {}).get(shift_type_uid)
    if shift is None:
        ui.notify("Schichtdaten nicht gefunden.", type="negative")
        return
    shift_type = instance.shift_types.get(shift_type_uid)
    if shift_type is None:
        ui.notify("Schichttyp nicht gefunden.", type="negative")
        return

    # Form data für Edit-Modus
    form_data = {
        "preffert_number_employees": shift.preffert_number_employees,
        "weight_below_preferred": shift.weight_below_preferred,
        "weight_above_preferred": shift.weight_above_preferred,
        "assign_employee_day_shift": shift.assign_employee_day_shift.copy()
        if shift.assign_employee_day_shift
        else set(),
        "ban_employee_day_shift": shift.ban_employee_day_shift.copy()
        if shift.ban_employee_day_shift
        else set(),
        "penalty_assigned_day_employee": shift.penalty_assigned_day_employee.copy()
        if shift.penalty_assigned_day_employee
        else {},
        "penalty_not_assigned_day_employee": shift.penalty_not_assigned_day_employee.copy()
        if shift.penalty_not_assigned_day_employee
        else {},
    }

    edit_mode = {"active": False}

    def save_shift():
        """Speichert die Änderungen an der Schicht."""
        try:
            # Validierung
            if form_data["preffert_number_employees"] < 0:
                ui.notify("Bevorzugte Anzahl kann nicht negativ sein", type="warning")
                return

            if form_data["weight_below_preferred"] < 0:
                ui.notify(
                    "Gewicht Unterbesetzung kann nicht negativ sein", type="warning"
                )
                return

            if form_data["weight_above_preferred"] < 0:
                ui.notify(
                    "Gewicht Überbesetzung kann nicht negativ sein", type="warning"
                )
                return

            # Aktualisiere Shift-Objekt direkt
            shift.preffert_number_employees = form_data["preffert_number_employees"]
            shift.weight_below_preferred = form_data["weight_below_preferred"]
            shift.weight_above_preferred = form_data["weight_above_preferred"]

            # Sichere Handhabung von Sets (können None sein)
            shift.assign_employee_day_shift = (
                form_data["assign_employee_day_shift"].copy()
                if form_data["assign_employee_day_shift"] is not None
                else set()
            )
            shift.ban_employee_day_shift = (
                form_data["ban_employee_day_shift"].copy()
                if form_data["ban_employee_day_shift"] is not None
                else set()
            )

            # Sichere Handhabung von Dicts (können None sein)
            shift.penalty_assigned_day_employee = (
                form_data["penalty_assigned_day_employee"].copy()
                if form_data["penalty_assigned_day_employee"] is not None
                else {}
            )
            shift.penalty_not_assigned_day_employee = (
                form_data["penalty_not_assigned_day_employee"].copy()
                if form_data["penalty_not_assigned_day_employee"] is not None
                else {}
            )

            # Stelle sicher, dass die Änderungen in der Instance gespeichert werden
            instance.shifts[day][shift_type_uid] = shift

            # Speichere geänderte Instance
            state.clear_solutions()
            state.set_instance(instance)

            ui.notify("Schicht erfolgreich aktualisiert", type="positive")

            # Zurück zum View-Modus
            edit_mode["active"] = False
            update_content()
            update_buttons()

        except Exception as e:
            ui.notify(f"Fehler beim Speichern: {str(e)}", type="negative")

    def toggle_edit_mode():
        """Wechselt zwischen View und Edit-Modus."""
        edit_mode["active"] = not edit_mode["active"]
        update_content()
        update_buttons()

    def update_content():
        """Aktualisiert den Dialog-Inhalt basierend auf dem Modus."""
        content_container.clear()

        with content_container:
            if edit_mode["active"]:
                # Edit-Modus: Eingabefelder
                with ui.column().classes("w-full gap-3"):
                    # Besetzungsanforderungen
                    with ui.card().classes("w-full mb-3 bg-blue-50"):
                        ui.label("Besetzungsanforderungen").classes(
                            "font-semibold mb-2"
                        )

                        ui.number(
                            label="Bevorzugte Anzahl Mitarbeiter",
                            min=0,
                            format="%d",
                        ).classes("w-full").bind_value(
                            form_data, "preffert_number_employees"
                        )

                        ui.number(
                            label="Gewicht Unterbesetzung",
                            min=0,
                            format="%d",
                        ).classes("w-full").bind_value(
                            form_data, "weight_below_preferred"
                        )

                        ui.number(
                            label="Gewicht Überbesetzung",
                            min=0,
                            format="%d",
                        ).classes("w-full").bind_value(
                            form_data, "weight_above_preferred"
                        )

                    # Mitarbeiter Zuweisungen/Sperren
                    with ui.card().classes("w-full mb-3 bg-green-50"):
                        ui.label("Mitarbeiter Zuweisungen").classes(
                            "font-semibold mb-2"
                        )

                        employee_options = {
                            uid: emp.name for uid, emp in instance.employees.items()
                        }

                        ui.select(
                            options=employee_options,
                            multiple=True,
                            label="Zugewiesene Mitarbeiter",
                        ).classes("w-full").bind_value(
                            form_data, "assign_employee_day_shift"
                        )

                        ui.select(
                            options=employee_options,
                            multiple=True,
                            label="Gesperrte Mitarbeiter",
                        ).classes("w-full").bind_value(
                            form_data, "ban_employee_day_shift"
                        )

                    # Strafpunkte
                    with ui.card().classes("w-full mb-3 bg-yellow-50"):
                        ui.label("Strafpunkte").classes("font-semibold mb-2")
                        ui.label(
                            "Wählen Sie einen Mitarbeiter aus und setzen Sie die Strafpunkte"
                        ).classes("text-sm text-gray-600 mb-2")

                        if instance.employees:
                            penalty_assigned = form_data[
                                "penalty_assigned_day_employee"
                            ].copy()
                            penalty_not_assigned = form_data[
                                "penalty_not_assigned_day_employee"
                            ].copy()

                            current_employee_uid = next(iter(instance.employees.keys()))

                            def update_penalty_fields(emp_uid):
                                assigned_input.value = penalty_assigned.get(emp_uid, 0)
                                not_assigned_input.value = penalty_not_assigned.get(
                                    emp_uid, 0
                                )

                            def save_penalty_assigned():
                                value = assigned_input.value
                                if value is not None and value > 0:
                                    penalty_assigned[current_employee_uid] = int(value)
                                elif current_employee_uid in penalty_assigned:
                                    del penalty_assigned[current_employee_uid]
                                form_data["penalty_assigned_day_employee"] = (
                                    penalty_assigned.copy()
                                )

                            def save_penalty_not_assigned():
                                value = not_assigned_input.value
                                if value is not None and value > 0:
                                    penalty_not_assigned[current_employee_uid] = int(
                                        value
                                    )
                                elif current_employee_uid in penalty_not_assigned:
                                    del penalty_not_assigned[current_employee_uid]
                                form_data["penalty_not_assigned_day_employee"] = (
                                    penalty_not_assigned.copy()
                                )

                            def on_employee_change(e):
                                nonlocal current_employee_uid
                                save_penalty_assigned()
                                save_penalty_not_assigned()
                                current_employee_uid = e.value
                                update_penalty_fields(current_employee_uid)

                            ui.select(
                                options=employee_options,
                                label="Mitarbeiter",
                                value=current_employee_uid,
                                on_change=on_employee_change,
                            ).classes("w-full mb-2")

                            with ui.row().classes("w-full gap-2"):
                                assigned_input = ui.number(
                                    label="Strafpunkte bei Zuweisung",
                                    min=0,
                                    format="%d",
                                    on_change=save_penalty_assigned,
                                ).classes("flex-1")

                                not_assigned_input = ui.number(
                                    label="Strafpunkte bei Nicht-Zuweisung",
                                    min=0,
                                    format="%d",
                                    on_change=save_penalty_not_assigned,
                                ).classes("flex-1")

                            update_penalty_fields(current_employee_uid)

            else:
                # View-Modus: Nur Anzeige
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
                        ui.label(
                            f"{shift_type.length} min ({shift_type.length / 60:.1f}h)"
                        )

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
                        ui.label("Mitarbeiter Zuweisungen").classes(
                            "font-semibold mb-2"
                        )

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
                            for (
                                emp_uid,
                                penalty,
                            ) in shift.penalty_assigned_day_employee.items():
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

    with ui.dialog() as dialog, ui.card().classes("min-w-[600px]"):
        with ui.row().classes("w-full items-center justify-between mb-4"):
            ui.label(f"Schicht Details: Tag {day}, {shift_type.name}").classes(
                "text-xl font-bold"
            )

        # Container für den Inhalt
        content_container = ui.column().classes("w-full")

        # Buttons
        button_container = ui.row().classes("w-full justify-end gap-2 mt-4")

        def update_buttons():
            button_container.clear()
            with button_container:
                if edit_mode["active"]:
                    ui.button("Abbrechen", on_click=toggle_edit_mode).props("flat")
                    ui.button("Speichern", on_click=save_shift).props("color=primary")
                else:
                    ui.button(
                        "Bearbeiten", icon="edit", on_click=toggle_edit_mode
                    ).props("color=primary")
                    ui.button("Schließen", on_click=dialog.close).props("flat")

        update_content()
        update_buttons()

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

            # TODO Vergleichsmodus liste aktualisieren
            # Setze Instance im globalen State
            state.clear_solutions()
            state.set_instance(loaded_instance)

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
            render_shift_type_details(refresh_callback=update_instance_display)
            render_employee_details(refresh_callback=update_instance_display)
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
