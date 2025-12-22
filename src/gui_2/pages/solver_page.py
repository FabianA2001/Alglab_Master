from nicegui import ui

from .. import state


def solver_page():
    """Seite für Solver-Konfiguration und -Ausführung."""

    def update_instance_info() -> None:
        """Aktualisiert die Anzeige der Instance-Informationen."""
        instance_info.clear()

        with instance_info:
            current_instance = state.get_instance()
            if current_instance:
                ui.label(
                    f"✓ Instance geladen: {len(current_instance.employees)} Mitarbeiter, "
                    f"{len(current_instance.shift_types)} Schichttypen, "
                    f"{current_instance.number_of_days} Tage"
                ).classes("text-green-600")
            else:
                ui.label("✗ Keine Instance geladen").classes("text-orange-500")

    def update_solution_info() -> None:
        """Aktualisiert die Anzeige der Solution-Informationen."""
        solution_info.clear()

        with solution_info:
            current_solution = state.get_solution()
            if current_solution:
                ui.label(
                    f"✓ Solution vorhanden (Objective: {current_solution.objective_value:.2f})"
                ).classes("text-blue-600")
            else:
                ui.label("○ Keine Solution vorhanden").classes("text-gray-500")

    with ui.card().classes("w-full mb-4"):
        ui.label("Solver").classes("text-2xl font-bold mb-4")

        # Zeige aktuelle Instance/Solution Info
        with ui.column().classes("w-full gap-2"):
            instance_info = ui.column()
            solution_info = ui.column()

        update_instance_info()
        update_solution_info()

        ui.separator()

        # Solver-Steuerung
        ui.button(
            "Solver starten",
            icon="play_arrow",
            on_click=lambda: ui.notify("Solver würde hier starten", type="info"),
        ).props("color=positive" if state.get_instance() else "disable")
