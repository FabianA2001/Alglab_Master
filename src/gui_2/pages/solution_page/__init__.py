"""Solution Page - Hauptseite für Lösungsanzeige und -verwaltung."""

from nicegui import ui

from ....solution import Solution
from ... import state
from .comparison import render_solution_comparison
from .components import (
    render_basic_info,
    render_constraint_validation,
    render_employee_assignments,
    render_statistics,
)
from .helpers import load_available_solutions


def solution_page():
    """Hauptseite für die Lösungsanzeige und -verwaltung."""

    # State für Vergleichslösung
    comparison_solution = {"value": None}

    def load_solution(solution_name: str) -> None:
        """Lädt eine Solution und aktualisiert die Anzeige.

        Args:
            solution_name: Name der zu ladenden Solution-Datei
        """
        try:
            solution = Solution.from_json_file(solution_name)
            # Setze Solution im globalen State (verfügbar für alle Seiten)
            state.rest_solutions()
            state.add_solution(solution)
            state.set_instance(solution.instance)
            state.clear_changed_days()  # Zurücksetzen bei neuer Solution
            update_solution_display()
            refresh_comparison_select()  # Aktualisiere Vergleichsliste
            ui.notify(
                f"Solution '{solution_name}' erfolgreich geladen", type="positive"
            )
        except Exception as e:
            ui.notify(f"Fehler beim Laden: {str(e)}", type="negative")

    def load_comparison_solution(solution_index: str) -> None:
        """Lädt eine zweite Solution zum Vergleich aus dem State.

        Args:
            solution_index: Index der Solution im State (als String) oder "(Keine)"
        """
        if not solution_index or solution_index == "(Keine)":
            comparison_solution["value"] = None
            update_solution_display()
            return

        try:
            all_solutions = state.get_all_solutions()
            idx = int(solution_index)

            if 0 <= idx < len(all_solutions):
                assert "value" in comparison_solution
                comparison_solution["value"] = all_solutions[idx]  # type: ignore
                update_solution_display()
                ui.notify(f"Vergleichslösung #{idx} geladen", type="positive")
            else:
                ui.notify("Ungültiger Solution-Index", type="negative")
                comparison_solution["value"] = None
        except Exception as e:
            ui.notify(
                f"Fehler beim Laden der Vergleichslösung: {str(e)}", type="negative"
            )
            comparison_solution["value"] = None

    def get_comparison_options() -> list[str]:
        """Erstellt die Optionen für die Vergleichsauswahl aus dem State.

        Returns:
            Liste mit "(Keine)" und den verfügbaren Solutions aus dem State
        """
        all_solutions = state.get_all_solutions()[:-1]
        if not all_solutions:
            return ["(Keine)"]

        options = ["(Keine)"]
        for idx, sol in enumerate(all_solutions):
            # Erstelle aussagekräftige Labels mit Timestamp und Objective Value
            label = f"#{idx}: {sol.timestamp.strftime('%Y-%m-%d %H:%M')} (Obj: {sol.objective_value:.1f})"
            options.append(label)

        return options

    def get_solution_index_from_label(label: str) -> str:
        """Extrahiert den Index aus dem Label.

        Args:
            label: Label im Format "#idx: ..." oder "(Keine)"

        Returns:
            Index als String oder "(Keine)"
        """
        if label == "(Keine)" or not label:
            return "(Keine)"

        # Extrahiere den Index aus "#idx: ..."
        try:
            return label.split(":")[0].replace("#", "").strip()
        except:
            return "(Keine)"

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

            # Vergleichsansicht anzeigen wenn zweite Solution vorhanden
            if comparison_solution["value"] is not None:
                # A = Vergleichslösung (alt), B = aktuelle Lösung (neu)
                render_solution_comparison(
                    comparison_solution["value"], current_solution
                )

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

            # Hauptlösung auswählen
            with ui.row().classes("w-full gap-4 items-center"):
                solution_select = ui.select(
                    options=available_solutions,
                    label="Hauptlösung (A) auswählen",
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

            # Vergleichslösung auswählen
            ui.separator().classes("my-4")
            ui.label("Vergleichsmodus (optional)").classes("text-lg font-semibold")
            ui.label(
                "Wählen Sie eine zweite Lösung aus dem State zum Vergleich"
            ).classes("text-sm text-gray-600 mb-2")

            @ui.refreshable
            def comparison_select_ui():
                ui.select(
                    options=get_comparison_options(),
                    label="Vergleichslösung (B) auswählen",
                    value="(Keine)",
                    on_change=lambda e: load_comparison_solution(
                        get_solution_index_from_label(e.value)
                    ),
                ).classes("w-full")

            def refresh_comparison_select():
                """Aktualisiert die Vergleichsauswahl."""
                try:
                    comparison_select_ui.refresh()
                except (RuntimeError, AttributeError):
                    # UI nicht mehr verfügbar
                    pass

            comparison_select_ui()

    # Container für die Solution-Anzeige
    solution_container = ui.column().classes("w-full")

    # Zeige aktuelle Solution beim Laden der Seite
    if state.get_solution() is not None:
        update_solution_display()
