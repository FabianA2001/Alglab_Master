from nicegui import ui


def bar():
    """Navigationsleiste für die Anwendung."""
    with ui.header().classes("items-center justify-between"):
        ui.label("Scheduler Optimization").classes("text-xl font-bold")
        with ui.row():
            ui.link("Instance", "/instance").classes("text-white")
            ui.link("Solver", "/solver").classes("text-white")
            ui.link("Solution", "/solution").classes("text-white")
