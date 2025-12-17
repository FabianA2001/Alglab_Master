from datetime import datetime

from ortools.sat.python import cp_model
from pydantic import BaseModel, Field
from typing import List, Tuple, Set

from .. import shift_vars
from ..inputTypes import instace
from ..module import (
    cover_requirements,
    days_off,
    limited_shifts_per_type_validation,
    max_Cons_Shifts,
    max_weekend_days,
    minimum_consecutive_days_off,
    minimum_consecutive_shifts,
    minMaxWorkTime,
    shift_assignment_single_day_validation,
    shift_rotation_constraint,
)
from ..module.solverConstraints import SolverConstraints
from ..solution import Solution


class Callback_Top_Solutions(cp_model.CpSolverSolutionCallback):

    def __init__(self, instance: instace.Instance, vars: shift_vars.Shift_vars, disabled_constraints: list[SolverConstraints] = [], start_time=None):
        super().__init__()
        self.instance = instance
        self.vars = vars
        self.top_solutions = []  # To store the top solutions
        self.ratio_wishes = 0.5  # Overall wishes ratio to fulfill
        self.ratio_below_pref = 0.5  # Threshold for daily staffing
        self.employee_ratio = 0.8  # Desired fulfillment ratio for each employee
        self.best_solution = None  # Variable to store best solution
        self.disabled_constraints = disabled_constraints  # Store the list of disabled constraints
        self.start_time = start_time  # Store the starting time

    def on_solution_callback(self):
        total_positive_weights = {emp: 0 for emp in self.instance.employees}  # Total positive weights per employee
        total_negative_weights = {emp: 0 for emp in self.instance.employees}  # Total negative weights per employee
        fulfilled_positive_wishes = {emp: 0 for emp in self.instance.employees}  # Fulfilled positive wishes
        fulfilled_negative_wishes = {emp: 0 for emp in self.instance.employees}  # Fulfilled negative wishes

        for day, day_shift_dict in self.instance.shifts.items():
            for type_uid, shift in day_shift_dict.items():
                pref = shift.preffert_number_employees
                below = self.Value(self.vars.below_prefferd_vars[(day, type_uid)])
                if below > pref * self.ratio_below_pref:
                    return  # Stop if the day is not sufficiently filled

                for emp in self.instance.employees:
                    weight_pos = shift.penalty_assigned_day_employee.get(emp, 0)
                    weight_neg = shift.penalty_not_assigned_day_employee.get(emp, 0)

                    # Positive wishes logic
                    if weight_pos > 0:
                        total_positive_weights[emp] += 1  # Count this positive wish
                        if self.Value(self.vars.vars[(day, type_uid, emp)]) == 1:
                            fulfilled_positive_wishes[emp] += 1  # Increment fulfilled positive wishes

                    # Negative wishes logic
                    if weight_neg > 0:
                        total_negative_weights[emp] += 1  # Count this negative wish
                        if self.Value(self.vars.vars[(day, type_uid, emp)]) == 0:
                            fulfilled_negative_wishes[emp] += 1  # Increment fulfilled negative wishes

        # Calculate fulfillment ratios for positive wishes and count employees meeting criteria
        positive_ratio_counts = 0
        negative_ratio_counts = 0

        for emp in self.instance.employees:
            # Positive wishes ratio check
            if total_positive_weights[emp] > 0:  # Avoid division by zero
                positive_fulfillment_ratio = fulfilled_positive_wishes[emp] / total_positive_weights[emp]
                if positive_fulfillment_ratio >= self.employee_ratio:  # Check if employee meets the desired ratio
                    positive_ratio_counts += 1  # Count meeting positive ratio

            # Negative wishes ratio check
            if total_negative_weights[emp] > 0:  # Avoid division by zero
                negative_fulfillment_ratio = fulfilled_negative_wishes[emp] / total_negative_weights[emp]
                if negative_fulfillment_ratio >= self.employee_ratio:  # Check if employee meets the desired employee ratio
                    negative_ratio_counts += 1  # Count meeting negative ratio

        if positive_ratio_counts == 0 and negative_ratio_counts == 0:  # Return early if no employee meets the ratio
            return

        # Calculate overall solution ratio considering all fulfilled positive wishes
        total_fulfilled_positive = sum(fulfilled_positive_wishes.values())
        total_weighted_positive = sum(total_positive_weights.values())

        solution_ratio = (
            total_fulfilled_positive / total_weighted_positive if total_weighted_positive > 0 else 0
        )

        # Count employees meeting positive and negative wishes that exceed the defined ratio_wishes
        positive_fulfillment_count = sum(1 for emp in self.instance.employees 
                                          if (total_positive_weights[emp] > 0 and 
                                              (fulfilled_positive_wishes[emp] / total_positive_weights[emp]) >= self.ratio_wishes))

        negative_fulfillment_count = sum(1 for emp in self.instance.employees 
                                          if (total_negative_weights[emp] > 0 and 
                                              (fulfilled_negative_wishes[emp] / total_negative_weights[emp]) >= self.ratio_wishes))


        # Calculate general ratio
        general_ratio = (
            (positive_fulfillment_count + negative_fulfillment_count) / (2 * len(self.instance.employees))
            if len(self.instance.employees) > 0 else 0
        )

        # Use general_ratio for storing top solutions instead of solution_ratio
        solution_ratio = general_ratio
        
        # Store the top solutions based on the overall solution ratio
        if len(self.top_solutions) < 3:
            self.top_solutions.append((solution_ratio, self.store_solution()))
        else:
            min_ratio = min(self.top_solutions, key=lambda x: x[0])[0]
            if solution_ratio > min_ratio:
                # Replace the solution with the lowest ratio
                self.top_solutions = [sol for sol in self.top_solutions if sol[0] != min_ratio]
                self.top_solutions.append((solution_ratio, self.store_solution()))
        
        if self.top_solutions:
            top_solution = max(self.top_solutions, key=lambda x: x[0])  # (ratio, solution)
            best_ratio, self.best_solution = top_solution  # Unpacking

    def store_solution(self) -> Solution:
        """Stores the solution in a new Solution instance and returns it."""
        solution = Solution(self.instance)  # Create a new instance of Solution

        for day in range(self.instance.number_of_days):
            for type_uid in self.instance.shifts[day]:
                for employee_uid in self.instance.employees:
                    var_value = self.Value(
                        self.vars.get_var(day, type_uid, employee_uid)
                    )
                    solution.set_var(day, type_uid, employee_uid, var_value)

        for weekend in range(round(self.instance.number_of_days / 7)):
            for employee_uid in self.instance.employees:
                weekend_value = self.Value(
                    self.vars.get_weekend_var(weekend, employee_uid)
                )
                solution.set_weekend_var(weekend, employee_uid, weekend_value)

        for day in range(self.instance.number_of_days):
            for type_uid in self.instance.shifts[day]:
                above_value = self.Value(
                    self.vars.get_above_prefferd_var(day, type_uid)
                )
                below_value = self.Value(
                    self.vars.get_below_prefferd_var(day, type_uid)
                )
                solution.set_above_prefferd_var(day, type_uid, above_value)
                solution.set_below_prefferd_var(day, type_uid, below_value)

        solution.objective_value = self.ObjectiveValue()
        solution.instance = self.instance
        solution.disabled_constraints = self.disabled_constraints
        solution.solve_status = cp_model.FEASIBLE
        if self.start_time is not None:
            solution.solve_time = (datetime.now() - self.start_time).total_seconds()
        else:
            solution.solve_time = 0  # Or handle it in another way as needed
        solution.timestamp = datetime.now()

        return solution  # Return the constructed solution