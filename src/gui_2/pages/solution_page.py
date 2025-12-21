from pathlib import Path

from nicegui import ui

from ...solution import Solution
from .. import state

# Constants
DATA_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data" / "solutions"


# Helper Functions
def load_available_solutions() -> list[str]:
    """Lädt alle verfügbaren Solution-Dateien aus dem DATA_DIR.

    Returns:
        list[str]: Sortierte Liste der Solution-Namen (ohne .json Endung)
    """
    if not DATA_DIR.exists():
        return []

    json_files = sorted([f.stem for f in DATA_DIR.glob("*.json")])
    return json_files


# UI Component Functions
def render_basic_info(solution: Solution) -> None:
    """Rendert die grundlegenden Informationen einer Solution.

    Args:
        solution: Die anzuzeigende Solution
    """
    with ui.card().classes("w-full mb-4"):
        ui.label("Grundlegende Informationen").classes("text-xl font-bold mb-2")
        ui.label(f"Timestamp: {solution.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        ui.label(f"Objective Value: {solution.objective_value:.2f}")
        ui.label(f"Solve Time: {solution.solve_time:.2f}s")
        ui.label(f"Solve Status: {solution.solve_status}")

        if solution.disabled_constraints:
            ui.label(
                f"Deaktivierte Constraints: {', '.join(c.name for c in solution.disabled_constraints)}"
            )


def render_constraint_validation(solution: Solution) -> None:
    """Rendert die Constraint-Validierung mit Details.

    Args:
        solution: Die zu validierende Solution
    """
    with ui.card().classes("w-full mb-4"):
        ui.label("Constraint-Validierung").classes("text-xl font-bold mb-2")
        all_valid, results = solution.checkt_constraints

        status_color = "positive" if all_valid else "negative"
        status_text = (
            "Alle Constraints erfüllt ✓" if all_valid else "Constraints verletzt ✗"
        )
        ui.label(status_text).classes(f"text-{status_color} font-bold")

        # Details zu einzelnen Constraints
        with ui.expansion("Constraint Details", icon="info").classes("w-full"):
            for constraint_name, (is_valid, violations) in results.items():
                icon = "check_circle" if is_valid else "error"
                color = "green" if is_valid else "red"

                with ui.row().classes("items-center gap-2"):
                    ui.icon(icon).props(f"color={color}")
                    ui.label(
                        f"{constraint_name}: {'✓' if is_valid else f'✗ ({len(violations)} Verstöße)'}"
                    )

                if violations and len(violations) <= 10:
                    for violation in violations[:10]:
                        ui.label(f"  • {violation}").classes(
                            "text-sm text-gray-600 ml-8"
                        )
                elif violations:
                    ui.label(
                        f"  ... und {len(violations) - 10} weitere Verstöße"
                    ).classes("text-sm text-gray-600 ml-8")


def render_statistics(solution: Solution) -> None:
    """Rendert die Statistiken einer Solution.

    Args:
        solution: Die Solution mit den anzuzeigenden Statistiken
    """
    with ui.card().classes("w-full mb-4"):
        ui.label("Statistiken").classes("text-xl font-bold mb-2")

        # Shift Fulfillment
        with ui.expansion("Schicht-Erfüllung", icon="event").classes("w-full"):
            ui.label(f"Minimal: {solution.minimal_shift_fulfillment():.2%}")
            ui.label(f"Maximal: {solution.maximum_shift_fulfillment():.2%}")
            ui.label(f"Durchschnitt: {solution.average_shift_fulfillment():.2%}")

        # Positive Wishes
        with ui.expansion("Positive Wünsche", icon="thumb_up").classes("w-full"):
            ui.label(f"Minimal: {solution.minimal_employee_positive_wishes_met():.2%}")
            ui.label(f"Maximal: {solution.maximum_employee_positive_wishes_met():.2%}")
            ui.label(
                f"Durchschnitt: {solution.average_employee_positive_wishes_met():.2%}"
            )
            ui.label(f"Median: {solution.median_employee_positive_wishes_met():.2%}")

        # Negative Wishes
        with ui.expansion("Negative Wünsche", icon="thumb_down").classes("w-full"):
            ui.label(f"Minimal: {solution.minimal_employee_negative_wishes_met():.2%}")
            ui.label(f"Maximal: {solution.maximum_employee_negative_wishes_met():.2%}")
            ui.label(
                f"Durchschnitt: {solution.average_employee_negative_wishes_met():.2%}"
            )
            ui.label(f"Median: {solution.median_employee_negative_wishes_met():.2%}")

        ui.label(f"Gesamt erfüllte Wünsche: {solution.total_fulfilled_wishes()}")


def render_employee_assignments(solution: Solution) -> None:
    """Rendert die Mitarbeiter-Zuordnungen pro Tag.

    Args:
        solution: Die Solution mit den Zuordnungen
    """
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


# Main Page Function
def solution_page():
    """Hauptseite für die Lösungsanzeige und -verwaltung."""

    def load_solution(solution_name: str) -> None:
        """Lädt eine Solution und aktualisiert die Anzeige.

        Args:
            solution_name: Name der zu ladenden Solution-Datei
        """
        try:
            solution = Solution.from_json_file(solution_name)
            # Setze Solution im globalen State (verfügbar für alle Seiten)
            state.set_solution(solution)
            update_solution_display()
            ui.notify(
                f"Solution '{solution_name}' erfolgreich geladen", type="positive"
            )
        except Exception as e:
            ui.notify(f"Fehler beim Laden: {str(e)}", type="negative")

    def update_solution_display() -> None:
        """Aktualisiert die Anzeige der Solution-Details."""
        solution_container.clear()

        current_solution = state.get_solution()
        if current_solution is None:
            with solution_container:
                ui.label("Keine Solution ausgewählt").classes("text-gray-500 italic")
            return

        with solution_container:
            render_basic_info(current_solution)
            render_constraint_validation(current_solution)
            render_statistics(current_solution)
            render_employee_assignments(current_solution)

    # UI Layout
    with ui.card().classes("w-full mb-4"):
        ui.label("Solution Viewer").classes("text-2xl font-bold mb-4")

        # Solution-Auswahl
        available_solutions = load_available_solutions()

        if not available_solutions:
            ui.label("Keine Solutions gefunden").classes("text-orange-500")
            ui.label(f"Pfad: {DATA_DIR}").classes("text-sm text-gray-500")
        else:
            ui.label(f"{len(available_solutions)} Solutions verfügbar").classes(
                "text-sm text-gray-600 mb-2"
            )

            with ui.row().classes("w-full gap-4 items-center"):
                solution_select = ui.select(
                    options=available_solutions,
                    label="Solution auswählen",
                    on_change=lambda e: load_solution(e.value) if e.value else None,
                ).classes("flex-grow")

                ui.button(
                    "Neu laden",
                    icon="refresh",
                    on_click=lambda: [
                        solution_select.set_options(load_available_solutions()),
                        ui.notify("Solutions aktualisiert", type="info"),
                    ],
                ).props("flat")

    # Container für die Solution-Anzeige
    solution_container = ui.column().classes("w-full")

    # Zeige aktuelle Solution beim Laden der Seite
    if state.get_solution() is not None:
        update_solution_display()
