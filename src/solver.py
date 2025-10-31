from ortools.sat.python import cp_model

from . import shift_vars
from .inputTypes import instace


class Solver:
    def __init__(self, instance: instace.Instance, vars: shift_vars.Shift_vars):
        self.instance = instance
        self.vars = vars.vars
        self.below_prefferd_vars = vars.below_prefferd_vars
        self.above_prefferd_vars = vars.above_prefferd_vars
        self.model = vars.model

    def solve(self):
        solver = cp_model.CpSolver()
        status = solver.Solve(self.model)
        if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
            print("Solution found:")
            for day in range(self.instance.number_of_days):
                for type_uid in self.instance.shifts[day]:
                    for employee_uid in self.instance.employees:
                        if solver.BooleanValue(
                            self.vars[(day, type_uid, employee_uid)]
                        ):
                            print(
                                f"Day {day}, Shift Type {type_uid} assigned to Employee {employee_uid}"
                            )
        else:
            print("No solution found.")

    def objevtive_value(self):
        objective_value = 0
        for employee_uid in self.instance.employees:
            for day in range(self.instance.number_of_days):
                for type_uid in self.instance.shifts[day]:
                    objective_value += self.instance.shifts[day][type_uid].penalty_not_assigned_day_employee[employee_uid]*(
                        1-self.vars[(day, type_uid, employee_uid)])
                    objective_value += self.instance.shifts[day][type_uid].penalty_assigned_day_employee[employee_uid]*self.vars[(
                        day, type_uid, employee_uid)]
        for day in range(self.instance.number_of_days):
            for type_uid in self.instance.shifts[day]:
                objective_value += self.below_prefferd_vars[day][type_uid] * \
                    self.instance.shifts[day][type_uid].weight_below_preferred
                objective_value += self.above_prefferd_vars[day][type_uid] * \
                    self.instance.shifts[day][type_uid].weight_above_preferred
        return objective_value
