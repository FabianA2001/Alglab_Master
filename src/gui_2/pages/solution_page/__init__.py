"""Solution Page - Hauptseite für Lösungsanzeige und -verwaltung."""

from nicegui import ui

from ....inputTypes import employee
from ....solution import Solution
from ....solve_employees import solve_employee
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
    # Arbeitskopie der aktuellen Solution für Änderungen
    # working_solution["changed_employees"] = {(day, shift_type_id): set[employee_uid]}
    working_solution: dict = {"value": None, "changed_employees": {}}

    def load_solution(solution_name: str) -> None:
        """Lädt eine Solution und aktualisiert die Anzeige.

        Args:
            solution_name: Name der zu ladenden Solution-Datei
        """
        try:
            solution = Solution.from_json_file(solution_name)
            # Setze Solution im globalen State (verfügbar für alle Seiten)
            state.rest_solutions()
            comparison_solution["value"] = None  # Zurücksetzen der Vergleichslösung
            state.add_solution(solution)
            state.set_instance(solution.instance)
            state.clear_changed_days()  # Zurücksetzen bei neuer Solution

            # Erstelle Arbeitskopie für Änderungen
            working_solution["value"] = solution.model_copy(deep=True)
            working_solution["changed_employees"] = {}  # Initialisiere Tracking

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
        except Exception:
            return "(Keine)"

    def add_changed_employee(employee_uid) -> None:
        """Fügt einen veränderten Mitarbeiter zum Tracking hinzu.

        Args:
            day: Tag der Änderung
            shift_type_id: Schicht-Typ ID
            employee_uid: Mitarbeiter UID
        """

        working_solution["changed_employees"] = employee_uid

    def get_changed_employees() -> employee.EmployeeUid:
        """Gibt das Dictionary mit veränderten Mitarbeitern zurück."""
        return working_solution["changed_employees"]

    def clear_changed_employees() -> None:
        """Löscht alle Tracking-Informationen für veränderte Mitarbeiter."""
        working_solution["changed_employees"] = None

    def commit_changes(test_emp=True) -> None:
        """Übernimmt Änderungen von der Arbeitskopie in den State."""
        if working_solution["value"] is None:
            ui.notify("Keine Arbeitskopie vorhanden", type="warning")
            return
        # TODO pass the new temp_solution after defining it
        if test_emp:
            changed_solutions = (
                state.get_changed_solution()
                if state.get_changed_solution()
                else state.get_solution()
            )
            assert changed_solutions is not None

            validity, temp_solution = solve_employee.st_solve_employee(
                get_changed_employees(),
                working_solution["value"].instance,
                in_solution=changed_solutions,
            )
            if not validity:
                print("teste änderung für employee_uid:", get_changed_employees())
                ui.notify(
                    "Änderung konnte nicht übernommen werden da die Instanze infeasible  werden würde",
                    type="warning",
                )
                clear_changed_employees()
                state_sol = state.get_solution()
                assert state_sol is not None
                working_solution["value"] = state_sol.model_copy(deep=True)
                # UI aktualisieren um die zurückgesetzten Werte anzuzeigen
                update_solution_display()
                refresh_comparison_select()
                return
            state.set_changed_solution(temp_solution)

        # Füge die geänderte Solution zum State hinzu
        state.add_solution(working_solution["value"])
        state.set_instance(working_solution["value"].instance)
        state_sol = state.get_solution()
        assert state_sol is not None
        working_solution["value"] = state_sol.model_copy(deep=True)

        # Lösche Tracking-Informationen nach Commit
        clear_changed_employees()

        # Aktualisiere die Anzeige
        update_solution_display()
        refresh_comparison_select()

        ui.notify("Änderungen erfolgreich übernommen", type="positive")

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

            # Shared current_week dictionary für beide Tabellen
            current_week = {"value": 0}

            # Container für comparison refresh callback
            comparison_refresh_container = {"refresh": None}

            def register_comparison_refresh(refresh_func):
                """Callback um die Refresh-Funktion der Vergleichstabelle zu speichern."""
                comparison_refresh_container["refresh"] = refresh_func

            # Rendere Haupttabelle und übergebe working_solution und commit callback
            assert working_solution["value"] is not None
            render_employee_assignments(
                working_solution["value"],
                current_week,
                lambda: comparison_refresh_container["refresh"]()
                if comparison_refresh_container["refresh"]
                else None,
                commit_changes,
                add_changed_employee,
            )
            # Vergleichsansicht anzeigen wenn zweite Solution vorhanden
            if comparison_solution["value"] is not None:
                # A = Vergleichslösung (alt), B = aktuelle Lösung (neu)
                render_solution_comparison(
                    comparison_solution["value"],
                    current_solution,
                    current_week,
                    register_comparison_refresh,
                )

    # UI Layout
    with ui.card().classes("w-full mb-4"):
        ui.label("Solution Viewer").classes("text-2xl font-bold mb-4")

        # Solution-Auswahl
        available_solutions = load_available_solutions()

        if not available_solutions:
            ui.label("Keine Solutions gefunden").classes("text-orange-500")
            ui.label("Pfad: data/solutions").classes("text-sm text-gray-500")
        elif state.is_solver_running():
            ui.label("Solver läuft ").classes("text-gray-500 italic")
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
    current_sol = state.get_solution()
    if current_sol is not None:
        # Erstelle Arbeitskopie für vorhandene Solution
        working_solution["value"] = current_sol.model_copy(deep=True)
        working_solution["changed_employees"] = {}  # Initialisiere Tracking
        update_solution_display()
