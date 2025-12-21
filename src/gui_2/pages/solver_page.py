from nicegui import ui


def solver_page():
    """Seite für Solver-Konfiguration."""
    with ui.card().classes("w-full"):
        ui.label("Solver").classes("text-2xl font-bold")
        ui.label("Hier kann der Solver konfiguriert werden.")
