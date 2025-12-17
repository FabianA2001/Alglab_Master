# solve_employee_script.py
import sys
import json
from src.solution import Solution
from src.parseData import parseTXT
from src.shift_vars import Shift_vars
from src.solver import Solver
from pathlib import Path
from src.module.solverConstraints import SolverConstraints
from src.inputTypes import instace, employee
from src.parseData import parseTXT
from ortools.sat.python import cp_model


def solve_employees_incrementally(employee_uids: list[employee.EmployeeUid], instance_data, soft_max_time_in_seconds:int=60):
    # Load instance from passed data
    DATA_DIR = (
        Path(__file__).resolve().parent / "data" / "instance_raw"
    )
    instance_data = instance_data + ".txt"
    path = DATA_DIR / instance_data
    instance = parseTXT.parse_txt(path)
    employee_copy = instance.employees.copy()
    instance.employees.clear()
    for employee_uid in employee_uids:
        instance.employees[employee_uid] = employee_copy[employee_uid]
    solver_ = Solver(instance, Shift_vars(instance))
    stop_after_first_solution = False
    if soft_max_time_in_seconds <= 8:
        soft_max_time_in_seconds = 450
        stop_after_first_solution = True
    if len(employee_uids)>1:
        previous_solution = Solution.from_json_file(str(employee_uids[-2]))
        solution = solver_.test_solution_validity(objective_function=solver_.objective_value_new, solution=previous_solution, log_search_progress=False, max_time_in_seconds=soft_max_time_in_seconds, stop_after_first_solution=stop_after_first_solution)
    else:
        solution = solver_.solve_callback_with_solution(objective_function=solver_.objective_value_new, log_search_progress=False, max_time_in_seconds=soft_max_time_in_seconds, stop_after_first_solution=stop_after_first_solution)
    
    if solution.solve_status in [cp_model.UNKNOWN]:
        if len(employee_uids)>1:
            previous_solution = Solution.from_json_file(str(employee_uids[-2]))
            solution = solver_.test_solution_validity(objective_function=solver_.objective_value_new, solution=previous_solution, log_search_progress=False, max_time_in_seconds=450, stop_after_first_solution=True)
        else:
            solution = solver_.solve_callback_with_solution(objective_function=solver_.objective_value_new, log_search_progress=False, max_time_in_seconds=450, stop_after_first_solution=True)
    return solution

if __name__ == "__main__":
    # Read input from command-line arguments
    employee_uids_str = sys.argv[1].split(',')  # Assuming input is comma-separated
    instance_data = sys.argv[2]
    soft_max_time_in_seconds = int(sys.argv[3])

    # Convert string UIDs to employee.EmployeeUid instances
    employee_uids = [employee.EmployeeUid(int(uid)) for uid in employee_uids_str]
    # Call the function with the transformed inputs
    solution = solve_employees_incrementally(employee_uids=employee_uids, instance_data=instance_data, soft_max_time_in_seconds=soft_max_time_in_seconds)

    solution.to_json_file(str(employee_uids[-1]))