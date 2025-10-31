from pathlib import Path

import pandas as pd
import taipy.gui.builder as tgb
from taipy.gui import Gui, Icon, navigate

from .. import shift_vars, solver
from ..inputTypes import instace
from ..parseData import parseTXT
from .parse_solution_to_table import parse_solution_to_table

DEFAULT_PATH = Path.joinpath(
    Path(__file__).resolve().parent.parent.parent, "data", "Instance1.txt"
)


def start_gui():
    inst: instace.Instance = parseTXT.parse_txt(DEFAULT_PATH)
    solver_instance = solver.Solver(inst, shift_vars.Shift_vars(inst))

    beispiel_option = True
    solution_data = pd.DataFrame({"Test1": [1, 2, 3], "Test2": [4, 5, 6]})

    def button_start_solve(state, action, info):
        solved_solution = solver_instance.solve(log_search_progress=False)
        state.solution_data = parse_solution_to_table(solved_solution)

    with tgb.Page() as page_1:
        tgb.text("# Instance", mode="md")

    with tgb.Page() as page_2:
        tgb.text("# Solver", mode="md")
        tgb.text("## Parameter", mode="md")
        with tgb.layout():
            with tgb.part():
                tgb.text("Beipsiel Option")
            with tgb.part():
                tgb.toggle("{beispiel_option}")
        tgb.text("Toggel ist {beispiel_option}")
        tgb.button("Start Solve", on_action=button_start_solve)

        tgb.text("## Solver Ergebniss", mode="md")
        tgb.table("{solution_data}", auto_loading=True, rebuild=True)

    def menu_option_selected(state, action, info):
        page = info["args"][0]
        navigate(state, to=page)

    with tgb.Page() as root_page:
        tgb.menu(
            label="Menu",
            lov=[
                ("page1", Icon("images/map.png", "Instance")),
                ("page2", Icon("images/person.png", "Solver")),
            ],
            on_action=menu_option_selected,
        )

    # TODO: add an about page to discuss the application and its features
    pages = {"/": root_page, "page1": page_1, "page2": page_2}

    Gui(pages=pages).run(title="Alglab Master", dark_mode=False)
