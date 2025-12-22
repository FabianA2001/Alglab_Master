"""Solution Page - Hauptseite für Lösungsanzeige und -verwaltung."""

from nicegui import ui

from ....solution import Solution
from ... import state
from .components import (
    render_basic_info,
    render_constraint_validation,
    render_employee_assignments,
    render_statistics,
)
from .helpers import load_available_solutions


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
            state.set_instance(solution.instance)
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
            ui.label("Pfad: data/solutions").classes("text-sm text-gray-500")
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
