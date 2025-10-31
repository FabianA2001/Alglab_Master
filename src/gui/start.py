from pathlib import Path

from taipy.gui import Gui

from .. import shift_vars, solver
from ..inputTypes import instace
from ..parseData import parseTXT

DEFAULT_PATH = Path.joinpath(
    Path(__file__).resolve().parent.parent.parent, "data", "Instance1.txt"
)


def start_gui():
    inst: instace.Instance = parseTXT.parse_txt(DEFAULT_PATH)
    solver_instance = solver.Solver(inst, shift_vars.Shift_vars(inst))

    # Initialisiere als None für Taipy State
    solution_result = None

    # Berechne instance_info_display einmal - MUSS VOR page definiert werden
    instance_info_display = f"""## Instance Info
- number of shift typs: {len(inst.shift_types)}
- number of employees: {len(inst.employees)}
"""

    def on_button_click(state):
        state.solution_result = solver_instance.solve(log_search_progress=False)

    # Hauptseite mit Modulen - NACH den Variablen definieren
    page = f"""
## Solver
<|Solve|button|on_action=on_button_click|>  
<|{instance_info_display}|>
### Result
<|{{solution_result.objective_value if solution_result else "No solution available."}}|text|>
"""

    gui = Gui(page)
    gui.run(title="Alglab Master", debug=True, dark_mode=False, use_reloader=True)
