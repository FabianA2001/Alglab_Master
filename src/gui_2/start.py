from nicegui import ui

from .components import bar
from .pages import instance_page, solution_page, solver_page


@ui.page("/")
def index():
    ui.navigate.to("/instance")


@ui.page("/instance")
def instance():
    bar()
    with ui.column().classes("w-full p-4"):
        instance_page()


@ui.page("/solver")
def solver():
    bar()
    with ui.column().classes("w-full p-4"):
        solver_page()


@ui.page("/solution")
def solution():
    bar()
    with ui.column().classes("w-full p-4"):
        solution_page()


def main():
    """Startet die NiceGUI-Anwendung."""
    ui.run(title="Scheduler Optimization")


if __name__ in {"__main__", "__mp_main__"}:
    main()
