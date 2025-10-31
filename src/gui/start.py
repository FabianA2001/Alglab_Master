from pathlib import Path

from taipy.gui import Gui

from .. import shift_vars, solver
from ..inputTypes import instace
from ..parseData import parseTXT
from .components import main_solver_component

DEFAULT_PATH = Path.joinpath(
    Path(__file__).resolve().parent.parent.parent, "data", "Instance1.txt"
)


def start_gui():
    inst: instace.Instance = parseTXT.parse_txt(DEFAULT_PATH)
    solver_instance = solver.Solver(inst, shift_vars.Shift_vars(inst))

    # Initialisiere als None für Taipy State
    solution_result = None

    def show_solution_text(state):
        if state.solution_result is None:
            return "No solution available."
        else:
            return f"Solution found with objective value: {state.solution_result.objective_value}"

    # Hauptseite mit Modulen
    page = main_solver_component(inst=inst)

    def on_button_click(state):
        state.solution_result = solver_instance.solve()

    gui = Gui(page)
    gui.run(title="Alglab Master", debug=True, dark_mode=False, use_reloader=True)
