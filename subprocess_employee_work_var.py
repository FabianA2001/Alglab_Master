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
from ortools.sat.python import cp_model

def solve_employee(employee_uid, instance_data, solution_name, soft_max_time_in_seconds:int=60):
    # Load instance from passed data
    DATA_DIR = (
        Path(__file__).resolve().parent / "data" / "instance_raw"
    )
    instance_data = instance_data + ".txt"
    path = DATA_DIR / instance_data
    instance = parseTXT.parse_txt(path)
    instance.employees = {int(employee_uid): instance.employees[int(employee_uid)]}
    
    solution_one_shift_type = Solution.from_json_file(solution_name)

    # Create your ShiftVars and Solver as before
    solver_ = Solver(instance, Shift_vars(instance))
    stop_after_first_solution = True
    if soft_max_time_in_seconds <= 8:
        soft_max_time_in_seconds = 450
        stop_after_first_solution = True

    solution = solver_.test_solution_validity(solution=solution_one_shift_type,
        disabled_constraints=[SolverConstraints.cover_requirements],
        objective_function=solver_.objective_value_new,
        log_search_progress=False,
        max_time_in_seconds=soft_max_time_in_seconds,
        stop_after_first_solution=stop_after_first_solution
    )

    solve_normally = False
    if solution.solve_status in [cp_model.UNKNOWN, cp_model.INFEASIBLE]:
        solve_normally = True
    
    if solve_normally:
        del solution
        del solver_
        instance1 = parseTXT.parse_txt(path)
        instance1.employees = {int(employee_uid): instance1.employees[int(employee_uid)]}
        #TODO you should create new solvers for the others files and functions
        solver_x = Solver(instance1, Shift_vars(instance1))
        solution1 = solver_x.solve_callback_with_solution(
            objective_function=solver_x.objective_value_only_wishes,
            log_search_progress=False,
            max_time_in_seconds=450,
            stop_after_first_solution=True
        )
        #TODO Unknown to check if an employee was bad (should find a better way in the feature)
        solution1.solve_status = cp_model.UNKNOWN
        return solution1
    return solution

if __name__ == "__main__":
    # Read input from command-line arguments
    employee_uid = sys.argv[1]
    instance_data = sys.argv[2]
    soft_max_time_in_seconds = int(sys.argv[3])
    solution_name = sys.argv[4]
    
    solution = solve_employee(employee_uid, instance_data, solution_name, soft_max_time_in_seconds)
    solution.to_json_file(employee_uid)