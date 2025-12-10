import sys
from pathlib import Path
# Assuming other required imports
# from your_solver_module import Solver, parseTXT, Shift_vars, cp_model
from pathlib import Path
from typing import Optional
import json
from src.solution import Solution
from src.parseData import parseTXT
from src.shift_vars import Shift_vars
from src.solver import Solver
from src.solution import Solution
from typing import List
from ortools.sat.python import cp_model
import gc

def process_file_immediate(json_file, x, constraint_number, key):
    instance = parseTXT.parse_txt(json_file).model_copy(deep=True)
    solver = Solver(instance, Shift_vars(instance))

    filename = f"{instance.name}_{key}_immediate_first_{x}"  # Include x in the filename
    print("\n" + filename)
    solution = solver.solve_with_early_stop_immediate(log_search_progress=False, max_time_in_seconds=15*60, constraint_set = constraint_number).model_copy(deep=True)

    if solution.solve_status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
        solution.instance.name = filename
        solution.to_json_file(filename)
    else:
        with open("no_immediate_solution_found_new.txt", 'a') as file:
            file.write(filename + "\n")


if __name__ == "__main__":
    json_file_path = Path(sys.argv[1])
    x = sys.argv[2]  # Get x from command-line arguments
    constraint_number = int(sys.argv[3])
    key = sys.argv[4]
    process_file_immediate(json_file_path, x, constraint_number, key)
