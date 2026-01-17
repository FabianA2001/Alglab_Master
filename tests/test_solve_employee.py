from cpsat_utils.testing import AssertModelFeasible, AssertModelInfeasible
from ortools.sat.python import cp_model

import pytest

from pathlib import Path
from src.parseData import parseTXT
from src.solve_employees import solve_employee
from src.shift_vars import Shift_vars
from src.solver import Solver
from src.LNS import lns
import time


@pytest.mark.parametrize(
    ("instance,"),
    [
        ("instance5"),
        ("instance9"),
        ("instance12"),
        ("instance21"),
        ("instance14"),
    ],
)
def test_validity_of_produced_solution_one_shift_method_after_time_lns(instance):
    """Test if the returned solution is valid by testing if the original instance with the solution as hard constraint is valid"""
    with AssertModelFeasible() as model:
        
        start_time = time.time()
        test_file = Path(__file__).resolve().parent / "instance_raw" / f"{instance}.txt"
        instance = parseTXT.parse_txt(test_file)
        vars = Shift_vars(instance.model_copy(deep=True))
        solve_employee_obj = solve_employee(instance=instance.model_copy(deep=True))
        solution = solve_employee_obj.solve_instance_one_shift(
            one_shift_max_time=45,
            fixed_work_var_opt_max_time=45,
            general_optimization_max_time=0,
        )
        print(solution.objective_value)
        print(f"my time passed: {time.time() - start_time}")

        vars = Shift_vars(instance.model_copy(deep=True))
        solution = lns.LNS(sol_or_instance=solution, timeout_seconds=30).solve()
        # print("we are here")
        # if solution.solve_status in [cp_model.FEASIBLE, cp_model.OPTIMAL]:
        #     print("solution is fine x")
        #     filename = f"{instance}_fine_lns"
        #     # solution1 = solution.model_copy()
        #     # solution.to_json_file(filename)
        # else:
        #     print("solution is not fine")
        #     filename = f"{instance}_not_fine_lns"
        #     # solution1 = solution.model_copy(deep=True)
        #     # solution.to_json_file(filename)

        print(solution.objective_value)
        print(f"lns time passed: {time.time() - start_time}")

        assert solution.checkt_constraints[0]

        vars = Shift_vars(instance.model_copy(deep=True), model)
        solver = Solver(instance.model_copy(deep=True), vars)
        solution = solver.warm_start_generalized(
            hard_constraint_solution=solution.model_copy(deep=True),
            hint_solution=solution.model_copy(deep=True),
            Test_solution=True,
            max_time_in_seconds=450,
        )
        print(solution.objective_value)
        print(f"test time passed: {time.time() - start_time}")


# @pytest.mark.parametrize(
#     ("instance"),
#     [
#         ("instance5"),
#         ("instance9"),
#         ("instance12"),
#         ("instance21"),
#         ("instance14"),
#     ],
# )
# def test_validity_of_produced_solution_one_shift_method_first_solution(instance):
#     """Test if the returned solution is valid by testing if the original instance with the solution as hard constraint is valid"""
#     with AssertModelFeasible() as model:
#         start_time = time.time()
#         test_file = Path(__file__).resolve().parent.parent / "data" / "instance_raw" / f"{instance}.txt"
#         instance = parseTXT.parse_txt(test_file)
#         vars = Shift_vars(instance.model_copy(deep=True))
#         solve_employee_obj = solve_employee(instance=instance.model_copy(deep=True))
#         solution = solve_employee_obj.solve_instance_one_shift(
#             one_shift_max_time=0,
#             fixed_work_var_opt_max_time=0,
#             general_optimization_max_time=0,
#         )

#         assert solution.checkt_constraints[0]

#         vars = Shift_vars(instance.model_copy(deep=True), model)
#         solver = Solver(instance.model_copy(deep=True), vars)
#         solution = solver.warm_start_generalized(
#             hard_constraint_solution=solution.model_copy(deep=True),
#             hint_solution=solution.model_copy(deep=True),
#             Test_solution=True,
#             max_time_in_seconds=450,
#         )
#         print(solution.objective_value)
#         print(f"time passed: {time.time() - start_time}")


# @pytest.mark.parametrize(
#     ("instance,"),
#     [
#         ("instance5"),
#         ("instance9"),
#         ("instance12"),
#         ("instance21"),
#         ("instance14"),
#     ],
# )
# def test_validity_of_produced_solution_one_shift_method_after_time_solution(instance):
#     """Test if the returned solution is valid by testing if the original instance with the solution as hard constraint is valid"""
#     with AssertModelFeasible() as model:
#         start_time = time.time()
#         test_file = Path(__file__).resolve().parent.parent / "data" / "instance_raw" / f"{instance}.txt"
#         instance = parseTXT.parse_txt(test_file)
#         vars = Shift_vars(instance.model_copy(deep=True))
#         solve_employee_obj = solve_employee(instance=instance.model_copy(deep=True))
#         solution = solve_employee_obj.solve_instance_one_shift(
#             one_shift_max_time=45,
#             fixed_work_var_opt_max_time=45,
#             general_optimization_max_time=0,
#         )

#         assert solution.checkt_constraints[0]

#         vars = Shift_vars(instance.model_copy(deep=True), model)
#         solver = Solver(instance.model_copy(deep=True), vars)
#         solution = solver.warm_start_generalized(
#             hard_constraint_solution=solution.model_copy(deep=True),
#             hint_solution=solution.model_copy(deep=True),
#             Test_solution=True,
#             max_time_in_seconds=450,
#         )
#         print(solution.objective_value)
#         print(f"time passed: {time.time() - start_time}")


# @pytest.mark.parametrize(
#     ("instance,"),
#     [
#         ("instance21"),
#     ],
# )
# def test_validity_of_produced_solution_one_shift_method_not_enough_time_case_work_var(
#     instance,
# ):
#     """Test if the returned solution is valid by testing if the original instance with the solution as hard constraint is valid, while also limiting the time intensely. Note that this is not an exact test"""
#     with AssertModelFeasible() as model:
#         start_time = time.time()
#         test_file = Path(__file__).resolve().parent.parent / "data" / "instance_raw" / f"{instance}.txt"
#         instance = parseTXT.parse_txt(test_file)
#         vars = Shift_vars(instance.model_copy(deep=True))
#         solve_employee_obj = solve_employee(instance=instance.model_copy(deep=True))
#         solution = solve_employee_obj.solve_instance_one_shift(
#             one_shift_max_time=45,
#             fixed_work_var_opt_max_time=2,
#             general_optimization_max_time=0,
#         )
#         vars = Shift_vars(instance.model_copy(deep=True), model)
#         solver = Solver(instance.model_copy(deep=True), vars)

#         assert solution.checkt_constraints[0]

#         solution = solver.warm_start_generalized(
#             hard_constraint_solution=solution.model_copy(deep=True),
#             hint_solution=solution.model_copy(deep=True),
#             Test_solution=True,
#             max_time_in_seconds=450,
#         )
#         print(solution.objective_value)
#         print(f"time passed: {time.time() - start_time}")


# @pytest.mark.parametrize(
#     ("instance,"),
#     [
#         ("instance21"),
#     ],
# )
# def test_validity_of_produced_solution_one_shift_method_not_enough_time_case_last_opt(
#     instance,
# ):
#     """Test if the returned solution is valid by testing if the original instance with the solution as hard constraint is valid, while also limiting the time intensely. Note that this is not an exact test"""
#     with AssertModelFeasible() as model:
#         start_time = time.time()
#         test_file = Path(__file__).resolve().parent.parent / "data" / "instance_raw" / f"{instance}.txt"
#         instance = parseTXT.parse_txt(test_file)
#         vars = Shift_vars(instance.model_copy(deep=True))
#         solve_employee_obj = solve_employee(instance=instance.model_copy(deep=True))
#         solution = solve_employee_obj.solve_instance_one_shift(
#             one_shift_max_time=45,
#             fixed_work_var_opt_max_time=2,
#             general_optimization_max_time=2,
#         )

#         assert solution.checkt_constraints[0]

#         vars = Shift_vars(instance.model_copy(deep=True), model)
#         solver = Solver(instance.model_copy(deep=True), vars)
#         solution = solver.warm_start_generalized(
#             hard_constraint_solution=solution.model_copy(deep=True),
#             hint_solution=solution.model_copy(deep=True),
#             Test_solution=True,
#             max_time_in_seconds=450,
#         )
#         print(solution.objective_value)
#         print(f"time passed: {time.time() - start_time}")
