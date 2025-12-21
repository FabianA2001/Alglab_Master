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
from src.solve_employees import solve_employee
import gc

def process_file(json_file, x, optimize: bool = False, incrementally: bool = False, soft_max_time_in_seconds: int=30*60, till_time: bool=False):
    instance = parseTXT.parse_txt(json_file).model_copy(deep=True)
    solver_employee = solve_employee(instance)

    filename = f"{instance.name}_optimize{optimize}_incrementally{incrementally}_immediate_first_{x}"  # Include x in the filename
    print("\n" + filename)
    solution = solver_employee.solve_all_employees_subprocess(incrementally=incrementally, optimize_till_max_time=optimize, soft_max_time_in_seconds=soft_max_time_in_seconds)

    if optimize and not till_time:
        if solution.solve_status in [cp_model.OPTIMAL]:
            filename = f"{solution.instance.name}_incrementally{incrementally}_opt_{x}"
        else:
            filename = f"{solution.instance.name}_incrementally{incrementally}_timeout_{x}"
    elif optimize and till_time:
        filename = f"{solution.instance.name}_incrementally{incrementally}_time_out_30_{x}"
    elif not optimize:
        filename = f"{solution.instance.name}_incrementally{incrementally}_immediate_first_{x}"
    else:
        print("error")
        
    print("\n" + filename)
    instance_name=""+solution.instance.name
    if solution.solve_status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
        solution.instance.name = filename
        solution.to_json_file(filename)
    else:
        with open("no_solution_found_employee_solve.txt", 'a') as file:
            file.write(filename + "\n")

    if optimize and till_time and solution.solve_status in [cp_model.OPTIMAL]:
        filename = f"{instance_name}_incrementally{incrementally}_opt_{x}"
        solution.to_json_file(filename)

if __name__ == "__main__":
    json_file_path = Path(sys.argv[1])
    x = sys.argv[2]  # Get x from command-line arguments
    optimize = sys.argv[3] == "True"
    incrementally = sys.argv[4] == "True"
    soft_max_time_in_seconds = int(sys.argv[5])
    till_time = sys.argv[6] == "True"
    process_file(json_file_path, x, optimize=optimize, incrementally=incrementally, soft_max_time_in_seconds=soft_max_time_in_seconds, till_time=till_time)
