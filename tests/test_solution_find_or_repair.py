from cpsat_utils.testing import AssertModelFeasible, AssertModelInfeasible
from ortools.sat.python import cp_model

from src import shift_vars
from src.inputTypes import employee, instace, shiftType
from src.module import (
    cover_requirements,
    days_off,
    max_Cons_Shifts,
    max_weekend_days,
    minimum_consecutive_days_off,
    minimum_consecutive_shifts,
    minMaxWorkTime,
    shift_assignment_single_day_validation,
    shift_rotation_constraint,
    days_off_new,
    max_Cons_shifts_new,
    minimum_consecutove_days_off_new,
    minimum_consecutive_shifts_new,
)

from pathlib import Path
from src.parseData import parseTXT
from src.solve_employees import solve_employee
from src.shift_vars import Shift_vars
from src.solver import Solver


def test_validity_of_produced_solution_each_employee_separately_function():
    with AssertModelFeasible() as model:
        test_file = Path.joinpath(
            Path(__file__).resolve().parent.parent, "data", "instance_raw", "Instance9.txt"
        )
        instance = parseTXT.parse_txt(test_file)
        vars = shift_vars.Shift_vars(instance, model)
        solve_employee_obj = solve_employee(instance=instance)
        solution = solve_employee_obj.solve_all_employees_subprocess(incrementally=False)
        solver = Solver(instance, vars)
        solution = solver.test_solution_validity(solution=solution.model_copy(deep=True)).model_copy(deep=True)

def test_validity_of_produced_solution_with_consideration_of_previous_part_solutions():
    with AssertModelFeasible() as model:
        test_file = Path.joinpath(
            Path(__file__).resolve().parent.parent, "data", "instance_raw", "Instance9.txt"
        )
        instance = parseTXT.parse_txt(test_file)
        vars = shift_vars.Shift_vars(instance, model)
        solve_employee_obj = solve_employee(instance=instance)
        solution = solve_employee_obj.solve_all_employees_subprocess(incrementally=True)
        solver = Solver(instance, vars)
        solution = solver.test_solution_validity(solution=solution.model_copy(deep=True)).model_copy(deep=True)