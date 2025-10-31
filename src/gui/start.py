from pathlib import Path

from taipy.gui import Gui

from .. import shift_vars, solution, solver
from ..inputTypes import instace
from ..parseData import parseTXT
from .components import instance_info_component, solver_component

DEFAULT_PATH = Path.joinpath(
        Path(__file__).resolve().parent.parent.parent, "data", "Instance1.txt"
    )

def start_gui():
    inst: instace.Instance = parseTXT.parse_txt(DEFAULT_PATH)
    solver_instance = solver.Solver(inst, shift_vars.Shift_vars(inst))
    result = "noch nicht gesolved"
    
    # Hauptseite mit Modulen
    page = f"""
# Alglab Master GUI

{instance_info_component(DEFAULT_PATH, inst)}

{solver_component()}
"""
    
    def on_button_click(state):
        solution_result = solver_instance.solve()
        state.result = f"Solved! Ergebnis: {solution_result}"
    
    gui = Gui(page)
    gui.run(
        title="Alglab Master",
        debug=True,
        dark_mode=False,
        use_reloader=True
    )