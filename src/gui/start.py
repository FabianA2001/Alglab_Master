from pathlib import Path

from taipy.gui import Gui

from .. import shift_vars, solution, solver
from ..inputTypes import instace
from ..parseData import parseTXT

DEFAULT_PATH = Path.joinpath(
        Path(__file__).resolve().parent.parent.parent, "data", "Instance1.txt"
    )

inst :instace.Instance = parseTXT.parse_txt(DEFAULT_PATH)
solver_instance = solver.Solver(inst, shift_vars.Shift_vars(inst))

def start_gui():
    # Initial state variables
    result = "noch nicht gesolved"

    # Simple GUI layout mit Auto-Reload Script
    page = """
# Alglab Master GUI

<|Solve|button|on_action=on_button_click|>

## Result
<|{result}|text|>


"""

    # Callback function for button click
    def on_button_click(state):
        global solver_instance
        solution_result = solver_instance.solve()
        state.result = f"Solved! Ergebnis: {solution_result}"

    # Create and run the GUI
    gui = Gui(page)
    gui.run(
        title="Alglab Master",
        port=5000,
        dark_mode=False,
        debug=True,
        use_reloader=True
    )