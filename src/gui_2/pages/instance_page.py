from nicegui import ui


def instance_page():
    """Seite für Instance-Verwaltung."""
    with ui.card().classes("w-full"):
        ui.label("Instance").classes("text-2xl font-bold")
        ui.label("Hier können Instanzen verwaltet werden.")
