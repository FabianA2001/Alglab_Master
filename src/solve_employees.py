from datetime import datetime

from ortools.sat.python import cp_model
from pydantic import BaseModel, Field, model_validator

from typing import Callable, Tuple

from . import shift_vars
from .callback_early_stop import Callback_Early_Stop
from .solverCallback.callback_three_best_solutions import Callback_Top_Solutions
from .inputTypes import employee, instace
from .module.solverConstraints import SolverConstraints
from .solution import Solution
from .solver import Solver
from .solverCallback.callback_improvement_slowed import callback_improvement_slowed

import time

from pathlib import Path
from src.parseData import parseTXT
from src.shift_vars import Shift_vars


# TODO add a logger instead of all prints
class solve_employee:
    def __init__(self, instance: instace.Instance):
        self.instance = instance
        self.solve_time = 0
        self.solution = Solution(instance=instance)
        self.hint_solution = Solution(instance=instance)

    def solve_all_employees(
        self,
        incrementally: bool = False,
        soft_max_time_in_seconds: int = 15 * 60,
        optimize_till_max_time: bool = False,
    ) -> Solution:
        """
        A function that find the first solution for the instance (that was given to the constructor) in a fast way(by solving one employee at a time).
        The function solve each employee on their own if incrementally is not set or set to false(with optimization only on employee wishes). Otherwise, after solving an employee, its solution will be passed to the next instance as hard constraints. In case of incrementally = True, each instance contain a new employee and all previous ones, and is solved in consideration to employee wishes and day fullness preferences.
        If optimize_till_max_time is True after a first solution (or better first solution) is found the funciton continue until the time given in soft_max_time_in_seconds run out.
        At the very end self.solution and self.hint_solution get a reset.

        :param incrementally: If True the employees solutions will be added at top of each others. Otherwise, each employee will be solved separately(only employee wishes will be considered).
        :type incrementally: bool
        :param soft_max_time_in_seconds: Time the function need to maximally take, if set to 0, the function will find a solution as fast as it can. Otherwise it will try to find a possibly better solution.
        :type soft_max_time_in_seconds: int
        :param optimize_till_max_time: If True after finding the first solution the function will use CPSAT to improve on the solution until the remaining time in soft_max_time_in_seconds run out.
        :type optimize_till_max_time: bool
        :return: Description
        :rtype: Solution
        """
        count_ = 0
        start_time = time.time()
        employee_uids = []
        instance_name = "" + self.instance.name
        for employee_uid in self.instance.employees:
            count_ += 1
            print(count_)
            employee_uids.append(employee_uid)
            soft_max_time_in_seconds_employee = soft_max_time_in_seconds - int(
                time.time() - start_time
            )
            if (len(self.instance.employees) - len(employee_uids)) != 0:
                soft_max_time_in_seconds_employee = int(
                    soft_max_time_in_seconds_employee
                    / (len(self.instance.employees) - len(employee_uids))
                )
            if incrementally:
                solution_temp = self.solve_employees_incrementally(
                    employee_uids=employee_uids,
                    soft_max_time_in_seconds=soft_max_time_in_seconds_employee,
                )
            else:
                solution_temp = self.solve_employee(
                    employee_uid=employee_uid,
                    soft_max_time_in_seconds=soft_max_time_in_seconds_employee,
                )

            # Handle return code and output from subprocess
            if solution_temp.solve_status not in [cp_model.INFEASIBLE]:
                self.solution.store_solution_vars(
                    solution=solution_temp, employee_uid=employee_uid
                )
                self.solution.store_solution_work_vars(
                    solution=solution_temp, employee_uid=employee_uid
                )
            else:
                print(
                    f"Error solving for employee {employee_uid}: No solution has been found"
                )

        solver = Solver(self.instance, shift_vars.Shift_vars(self.instance))
        self.solution = solver.warm_start_generalized(
            hard_constraint_solution=self.solution,
            max_time_in_seconds=9999,
            objective_function=solver.objective_value_new,
            stop_after_first_solution=True,
        )
        end_time = time.time()
        self.solution.solve_time = end_time - start_time

        soft_max_time_in_seconds = soft_max_time_in_seconds - int(
            time.time() - start_time
        )
        if soft_max_time_in_seconds < 0:
            soft_max_time_in_seconds = 60
        self.instance.name = instance_name
        if optimize_till_max_time:
            solver = Solver(self.instance, shift_vars.Shift_vars(self.instance))
            solution = solver.warm_start_generalized(
                hint_solution=self.solution,
                max_time_in_seconds=soft_max_time_in_seconds,
                objective_function=solver.objective_value_new,
            )
            solution.solve_time = end_time - start_time
            end_time = time.time()
            execution_time = end_time - start_time
            print(f"Execution time 2: {execution_time:.6f} seconds")
            return solution
        solution = self.solution.model_copy(deep=True)
        self.solution = Solution(self.instance)
        return solution

    def solve_employee(
        self, employee_uid: employee.EmployeeUid, soft_max_time_in_seconds: int = 60
    ):
        """
        A function that for the instance passed in the constructor, get an instance that only contains the given employee and then solve this instance and employee until timeout for soft_max_time_in_seconds or first solution if soft_max_time_in_seconds <= 8.

        :param self: Description
        :param employee_uid: The employee to be solved
        :type employee_uid: employee.EmployeeUid
        :param soft_max_time_in_seconds: Time for the optimization of the solution (only considering employee wishes), if <= 8 then the first solution is given back.
        :type soft_max_time_in_seconds: int
        """
        start_time = time.time()
        instance_copy = self.instance.model_copy()
        instance_copy.employees = {employee_uid: instance_copy.employees[employee_uid]}
        solver_ = Solver(instance_copy, shift_vars.Shift_vars(instance_copy))
        stop_after_first_solution = False
        if soft_max_time_in_seconds <= 8:
            soft_max_time_in_seconds = 450
            stop_after_first_solution = True
        # also implement something to consider the previously set employees shifts
        solution = solver_.solve_callback_with_solution(
            disabled_constraints=[SolverConstraints.cover_requirements],
            objective_function=solver_.objective_value_only_wishes,
            log_search_progress=False,
            max_time_in_seconds=soft_max_time_in_seconds,
            stop_after_first_solution=stop_after_first_solution,
        )
        if solution.solve_status in [cp_model.UNKNOWN]:
            solution = solver_.solve_callback_with_solution(
                disabled_constraints=[SolverConstraints.cover_requirements],
                objective_function=solver_.objective_value_only_wishes,
                log_search_progress=True,
                max_time_in_seconds=450,
                stop_after_first_solution=True,
            )

        end_time = time.time()
        print(end_time - start_time)
        return solution

    def solve_employees_incrementally(
        self,
        employee_uids: list[employee.EmployeeUid],
        soft_max_time_in_seconds: int = 60,
        solution: Solution | None = None,
    ):
        """
        A function that solve an for the last employee in the employee_uids list, with consideration to all other employees in the list. For all other employees in the list their solution in the given solution is held while optimizing for the last employee. Or if no solution is given the solution of the self object is used.

        :param self: Description
        :param employee_uids: The employees to keep their solution up until the last employee which should be optimized.
        :type employee_uids: list[employee.EmployeeUid]
        :param soft_max_time_in_seconds: Time allowed for the optimization
        :type soft_max_time_in_seconds: int
        :param solution: A solution to get the values of the employees up until the last one in the list.
        :type solution: Solution | None
        """
        start_time = time.time()
        instance_copy = self.instance.model_copy()
        employee_copy = instance_copy.employees.copy()
        if solution is None:
            vars_dict = self.solution.vars
        else:
            vars_dict = solution.vars

        if len(employee_uids) > 1:
            for day in range(instance_copy.number_of_days):
                for type_uid in instance_copy.shifts[day]:
                    for employee_uid in employee_uids:
                        if employee_uid == employee_uids[-1]:
                            break
                        working = vars_dict[(day, type_uid, employee_uid)] == 1
                        instance_copy.shifts[day][
                            type_uid
                        ].preffert_number_employees = (
                            instance_copy.shifts[day][
                                type_uid
                            ].preffert_number_employees
                            - working
                        )
                    if (
                        instance_copy.shifts[day][type_uid].preffert_number_employees
                        < 0
                    ):
                        instance_copy.shifts[day][type_uid].weight_above_preferred = (
                            instance_copy.shifts[day][type_uid].weight_above_preferred
                            * (
                                -instance_copy.shifts[day][
                                    type_uid
                                ].preffert_number_employees
                                + 1
                            )
                        )
                        instance_copy.shifts[day][
                            type_uid
                        ].preffert_number_employees = 0

        instance_copy.employees.clear()
        instance_copy.employees = {employee_uids[-1]: employee_copy[employee_uids[-1]]}

        solver_ = Solver(instance_copy, shift_vars.Shift_vars(instance_copy))
        stop_after_first_solution = False
        if soft_max_time_in_seconds <= 8:
            soft_max_time_in_seconds = 450
            stop_after_first_solution = True

        solution = solver_.solve_callback_with_solution(
            objective_function=solver_.objective_value_new,
            log_search_progress=False,
            max_time_in_seconds=soft_max_time_in_seconds,
            stop_after_first_solution=stop_after_first_solution,
        )

        if solution.solve_status in [cp_model.UNKNOWN]:
            solver_ = Solver(instance_copy, shift_vars.Shift_vars(instance_copy))
            solution = solver_.solve_callback_with_solution(
                objective_function=solver_.objective_value_new,
                log_search_progress=False,
                max_time_in_seconds=450,
                stop_after_first_solution=True,
            )

        end_time = time.time()
        print(end_time - start_time)
        return solution

    # TODO Create a function in solution that create full solution from assigned shifts.
    def solve_instance_one_shift(
        self,
        one_shift_max_time: int = 0,
        fixed_work_var_opt_max_time: int = 0,
        general_optimization_max_time: int = 0,
        one_shift_callback: cp_model.CpSolverSolutionCallback | None = None,
        fixed_work_var_opt_callback: cp_model.CpSolverSolutionCallback | None = None,
        optimization_callback: cp_model.CpSolverSolutionCallback | None = None,
        constraint_set_opt: int = 2,
    ):
        """
        The function get a simplified instance (containing only one shift type) of the main instance and solve it, which result in work_var solution. Because the result maybe invalid, the solution for the work_var is validated for each employee and fixed if needed. After ward an optimization with the work_var variable as hard constraints is preformed. At the very end general optimization is preformed.

        :param self: Description
        :param one_shift_max_time: The maximum time (seconds) that the one shift solver is allowed to run (if 0 the solver stop after first solution) (if no solution was found in the time the solver will rerun, until first solution)
        :type one_shift_max_time: int
        :param fixed_work_var_opt_max_time: The maximum time (seconds) that the solver, with the work_var solution from one_shift solver as hard constraints, is allowed to run. (if 0 the solver stop after first solution) (if no solution was found in the time the solver will rerun, until first solution)
        :type fixed_work_var_opt_max_time: int
        :param general_optimization_max_time: The maximum time (seconds) that the optimization solver, with the solution from fixed_work_var solver as hint, is allowed to run. (if 0 no optimization of the fixed_work_var solution will be preformed) (if no solution was found in the time the solver will rerun, until first solution)
        :type general_optimization_max_time: int
        :param one_shift_callback: Callback to stop one shift solver
        :type one_shift_callback: cp_model.CpSolverSolutionCallback | None
        :param fixed_work_var_opt_callback: Callback to stop fixed_work_var solver
        :type fixed_work_var_opt_callback: cp_model.CpSolverSolutionCallback | None
        """
        if one_shift_callback is None:
            one_shift_callback = callback_improvement_slowed(
                percentual_improvement=0.025, time_between_checks_in_seconds=8
            )
        if fixed_work_var_opt_callback is None:
            fixed_work_var_opt_callback = callback_improvement_slowed(
                percentual_improvement=0.012, time_between_checks_in_seconds=8
            )

        input_tupel = (
            one_shift_max_time + 0,
            fixed_work_var_opt_max_time + 0,
            general_optimization_max_time + 0,
        )
        stop_after_first_solution = False
        if one_shift_max_time <= 0:
            one_shift_max_time = 450
            stop_after_first_solution = True
        counter = 0
        start_time = time.time()
        solution = Solution(instance=self.instance)

        # A loop that enforce finding a first solution unless the created one_shift instance is invalid
        while counter <= 1:
            instance = self.instance.instance_to_one_shift_type()
            solver = Solver(instance, shift_vars.Shift_vars(instance))
            solution = solver.solve_callback_with_solution(
                log_search_progress=False,
                max_time_in_seconds=one_shift_max_time,
                objective_function=solver.objective_value_new,
                stop_after_first_solution=stop_after_first_solution,
                disabled_constraints=[
                    SolverConstraints.shift_assignment_single_day_validation,
                    SolverConstraints.shift_rotation_constraint,
                    SolverConstraints.limited_shifts_per_type_validation,
                ],
                callback=one_shift_callback,
            )
            counter = counter + 1
            if solution.solve_status in [cp_model.FEASIBLE, cp_model.OPTIMAL]:
                break
            elif solution.solve_status in [cp_model.UNKNOWN]:
                one_shift_max_time = 450
                stop_after_first_solution = True
            elif solution.solve_status in [cp_model.INFEASIBLE, cp_model.MODEL_INVALID]:
                print("Something went wrong and the model is infeasible or invalid")
                return solution
            if counter == 2:
                return solution
        one_shift_time_end = time.time()
        end_time = time.time()
        print("one shift time: ", (end_time - start_time))
        solution.solve_time = end_time - start_time

        for employee_uid, employee_ in self.instance.employees.items():
            self.solution.store_solution_work_vars(
                solution=solution.model_copy(), employee_uid=employee_uid
            )

        # See if any employee does not have a solution with the given work days and repair their shifts if so.
        employees_uid = []
        count_ = 0
        invalid_employees = []
        for employee_uid in self.instance.employees:
            count_ = count_ + 1
            employees_uid.append(employee_uid)
            solution_temp, employee_work_var_was_invalid = (
                self.solve_employee_with_work_var(
                    employee_uid=employee_uid, soft_max_time_in_seconds=30
                )
            )
            self.hint_solution.copy_solution(solution=solution_temp.model_copy())
            if solution_temp.solve_status in [cp_model.FEASIBLE, cp_model.OPTIMAL]:
                if employee_work_var_was_invalid:
                    invalid_employees.append(self.instance.employees[employee_uid].name)
                    for day in range(self.instance.number_of_days):
                        self.solution.work_vars.pop((day, employee_uid))
            else:
                print(f"Error solving for employee {employee_uid}: ")

        employee_verification_time = time.time()
        self.hint_solution.solve_time = employee_verification_time - start_time
        print("verification time: ", employee_verification_time - one_shift_time_end)  # type: ignore
        self.hint_solution.set_preferred_vars()
        self.hint_solution.objective_value_new()
        self.hint_solution.calculate_work_vars()
        self.hint_solution.solve_status = cp_model.FEASIBLE
        self.hint_solution.timestamp = datetime.now()

        instance_name_ = self.instance.name + ""

        if fixed_work_var_opt_max_time > 0:
            fixed_work_var_opt_max_time = (
                fixed_work_var_opt_max_time
                + input_tupel[0]
                - int(time.time() - start_time)
            )

        if fixed_work_var_opt_max_time > 0:
            self.instance.name = instance_name_
            solver = Solver(self.instance, shift_vars.Shift_vars(self.instance))
            solution_temp = solver.warm_start_generalized(
                hard_constraint_solution=self.solution,
                hint_solution=self.hint_solution,
                max_time_in_seconds=fixed_work_var_opt_max_time,
                objective_function=solver.objective_value_new,
                stop_after_first_solution=False,
                callback=fixed_work_var_opt_callback,
                constraint_set=constraint_set_opt,
            )
            if solution_temp.solve_status in [cp_model.FEASIBLE, cp_model.OPTIMAL]:
                self.solution = solution_temp
            # Return the Hint because we could not find solution and optimize using normal solve with work_var
            elif solution_temp.solve_status in [cp_model.UNKNOWN]:
                self.solution = self.hint_solution.model_copy()
                print(
                    "Set Work_var: No solution found in the desired time, passing last found valid solution"
                )
            elif solution_temp.solve_status in [
                cp_model.INFEASIBLE,
                cp_model.MODEL_INVALID,
            ]:
                print("Something went wrong and the model is infeasible or invalid")
                return solution_temp
        else:
            print(
                "Set Work_var: Solution wanted in less than 0 seconds, Keeping last valid solution"
            )
            self.hint_solution.instance.name = self.instance.name + "_seedxxxxxxxx"
            self.solution = self.hint_solution.model_copy()

        work_var_opt_time = time.time()
        print("work_var time", work_var_opt_time - employee_verification_time)

        # Because we have input_tupel[0]+input_tupel[1]-int(time.time()-start_time)>0, this method may take more time than was initially desired but still in the desired time of the full function
        if (
            general_optimization_max_time > 0
            and input_tupel[0] + input_tupel[1] - int(time.time() - start_time) > 0
        ):
            general_optimization_max_time = (
                general_optimization_max_time
                + input_tupel[0]
                + input_tupel[1]
                - int(time.time() - start_time)
            )

        if general_optimization_max_time > 0:
            self.instance.name = instance_name_
            solver = Solver(self.instance, shift_vars.Shift_vars(self.instance))
            solution_temp = solver.warm_start_generalized(
                hint_solution=self.solution,
                max_time_in_seconds=general_optimization_max_time,
                objective_function=solver.objective_value_new,
                stop_after_first_solution=False,
                callback=optimization_callback,
                constraint_set=constraint_set_opt,
            )
            if solution_temp.solve_status in [cp_model.FEASIBLE, cp_model.OPTIMAL]:
                self.solution = solution_temp
            elif solution_temp.solve_status in [cp_model.UNKNOWN]:
                print(
                    "Opt: No solution was found in the desired time keeping last valid solution found"
                )
            elif solution_temp.solve_status in [
                cp_model.INFEASIBLE,
                cp_model.MODEL_INVALID,
            ]:
                print("Something went wrong and the model is infeasible or invalid")
                return solution_temp
        else:
            print("Opt: No general optimization desired, keeping last valid solution")

        # if len(invalid_employees)>0 or True:
        #     with open('invalid_employees_count.txt', 'a') as file:
        #         invalid_employees_string=f"\n{self.instance.name}_1S{input_tupel[0]}_wv{input_tupel[1]}_o{input_tupel[2]}: "+str(len(invalid_employees))+"/" +str(len(self.instance.employees.keys())) + f": {str(invalid_employees)} - time for employee verification is {employee_verification_time-one_shift_time_end} - time for opt work_var after employee verification is {work_var_opt_time-employee_verification_time}\n-{str(len(invalid_employees))},{employee_verification_time-one_shift_time_end},{work_var_opt_time-employee_verification_time}, {one_shift_time_end-start_time}, {time.time()-work_var_opt_time}"
        #         file.write(invalid_employees_string)

        end_time = time.time()
        print("optimization time", end_time - work_var_opt_time)
        self.solution.solve_time = end_time - start_time
        if general_optimization_max_time == 0 and self.solution.solve_status in [
            cp_model.OPTIMAL
        ]:
            self.solution.solve_status = cp_model.FEASIBLE
        solution_copy = self.solution.model_copy()
        self.solution = Solution(self.instance)

        return solution_copy

    def solve_employee_with_work_var(
        self, employee_uid, soft_max_time_in_seconds: int = 60
    ) -> Tuple[Solution, bool]:
        start_time = time.time()

        instance = self.instance.model_copy()
        instance.employees = {int(employee_uid): instance.employees[int(employee_uid)]}

        solution_one_shift_type = self.solution

        solver = Solver(instance, Shift_vars(instance))
        stop_after_first_solution = False
        if soft_max_time_in_seconds <= 8:
            soft_max_time_in_seconds = 450
            stop_after_first_solution = True

        solution = solver.warm_start_generalized(
            hard_constraint_solution=solution_one_shift_type,
            disabled_constraints=[SolverConstraints.cover_requirements],
            objective_function=solver.objective_value_new,
            log_search_progress=False,
            max_time_in_seconds=soft_max_time_in_seconds,
            stop_after_first_solution=stop_after_first_solution,
        )

        solve_normally = False
        if solution.solve_status in [cp_model.UNKNOWN, cp_model.INFEASIBLE]:
            solve_normally = True

        if solve_normally:
            # If we did not find a solution with the help of work_var, try to without them and only search for a first solution
            solver_x = Solver(instance, Shift_vars(instance))
            solution1 = solver_x.solve_callback_with_solution(
                objective_function=solver_x.objective_value_only_wishes,
                log_search_progress=False,
                max_time_in_seconds=450,
                stop_after_first_solution=True,
            )
            return (solution1, True)
        return (solution, False)

    @staticmethod
    def st_solve_employee(
        employee_uid: employee.EmployeeUid, instance: instace.Instance
    ):
        """
        A function that for the instance passed, get an instance that only contains the given employee and then solve this instance and employee, at the end it return True if a solution exist and the employee is valid and False otherwise.

        :param employee_uid: The employee to be solved
        :type employee_uid: employee.EmployeeUid
        :param instance: The instance
        :type instance: instace.Instance
        :return: True if the employee is valid with the instance False otherwise
        """

        start_time = time.time()
        original_employees = instance.employees.copy()
        instance_copy = instance
        instance_copy.employees = {employee_uid: instance_copy.employees[employee_uid]}
        solver_ = Solver(instance_copy, shift_vars.Shift_vars(instance_copy))
        # also implement something to consider the previously set employees shifts
        solution = solver_.solve_callback_with_solution(
            disabled_constraints=[SolverConstraints.cover_requirements],
            objective_function=solver_.objective_value_only_wishes,
            log_search_progress=False,
            max_time_in_seconds=60,
            stop_after_first_solution=True,
        )
        instance_copy.employees = original_employees
        print(time.time() - start_time)

        if solution.solve_status in [cp_model.FEASIBLE, cp_model.OPTIMAL]:
            return True
        elif solution.solve_status in [cp_model.UNKNOWN]:
            print("TOO SLOW")
            return False
        else:
            return False
