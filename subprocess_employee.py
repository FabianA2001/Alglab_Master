# solve_employee_script.py
import sys
import json
from src.solution import Solution
from src.parseData import parseTXT
from src.shift_vars import Shift_vars
from src.solver import Solver
from pathlib import Path
from src.module.solverConstraints import SolverConstraints
from src.inputTypes import instace
from src.parseData import parseTXT

def solve_employee(employee_uid, instance_data):
    # Load instance from passed data
    DATA_DIR = (
        Path(__file__).resolve().parent / "data" / "instance_raw"
    )
    instance_data = instance_data + ".txt"
    path = DATA_DIR / instance_data
    instance = parseTXT.parse_txt(path)
    instance.employees = {employee_uid: instance.employees[int(employee_uid)]}
    
    # Create your ShiftVars and Solver as before
    solver_ = Solver(instance, Shift_vars(instance))
    
    solution = solver_.solve_callback_with_solution(
        disabled_constraints=[SolverConstraints.cover_requirements],
        objective_function=solver_.objective_value_only_wishes,
        log_search_progress=False,
        max_time_in_seconds=450,
    )
    
    return solution

if __name__ == "__main__":
    # Read input from command-line arguments
    employee_uid = sys.argv[1]
    instance_data = sys.argv[2]
    
    solution = solve_employee(employee_uid, instance_data)
    solution.to_json_file(employee_uid)