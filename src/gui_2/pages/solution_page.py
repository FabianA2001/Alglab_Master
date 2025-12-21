from nicegui import ui


def solution_page():
    """Seite für Lösungsanzeige."""
    with ui.card().classes("w-full"):
        ui.label("Solution").classes("text-2xl font-bold")
        ui.label("Hier werden die Lösungen angezeigt.")
