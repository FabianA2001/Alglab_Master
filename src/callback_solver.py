from datetime import datetime

from ortools.sat.python import cp_model

from . import shift_vars
from .inputTypes import instace
from .module import (
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
from .module.solverConstraints import SolverConstraints
from .solution import Solution


class Callback_Solver(cp_model.CpSolverSolutionCallback):
    def __init__(self, instance: instace.Instance, vars: shift_vars.Shift_vars):
        super().__init__()
        self.instance = instance
        self.vars = vars
        self.solve_time = 0
        self.start_solve_time: datetime = datetime(2005, 1, 1, 0, 0)

    def on_solution_callback(self):
        check = 0
        wishes = 0
        for employee_uid in self.instance.employees:
            for day in range(self.instance.number_of_days):
                for type_uid in self.instance.shifts[day]:
                    if (
                        self.instance.get_shift(
                            day=day, type_uid=type_uid
                        ).penalty_assigned_day_employee.get(employee_uid, 0)
                        > 0
                    ):
                        wishes += 1 * self.Value(
                            self.vars.vars[(day, type_uid, employee_uid)]
                        )
                    if (
                        self.instance.get_shift(
                            day=day, type_uid=type_uid
                        ).penalty_not_assigned_day_employee.get(employee_uid, 0)
                        > 0
                    ):
                        wishes += 1 * (
                            1
                            - self.Value(self.vars.vars[(day, type_uid, employee_uid)])
                        )
        summ = 0
        for employee_uid in self.instance.employees:
            for day in range(self.instance.number_of_days):
                for type_uid in self.instance.shifts[day]:
                    if (
                        self.instance.get_shift(
                            day=day, type_uid=type_uid
                        ).penalty_assigned_day_employee.get(employee_uid, 0)
                        > 0
                    ):
                        summ += 1
                    if (
                        self.instance.get_shift(
                            day=day, type_uid=type_uid
                        ).penalty_not_assigned_day_employee.get(employee_uid, 0)
                        > 0
                    ):
                        summ += 1

        if wishes > 0.1 * summ:
            check = 1

        for day in range(self.instance.number_of_days):
            for type_uid in self.instance.shifts[day]:
                if (
                    self.Value(self.vars.below_prefferd_vars[(day, type_uid)])
                    / self.instance.shifts[day][type_uid].preffert_number_employees
                ) > 0.1:
                    check = 0
            # objective_value += (
            #     self.vars.above_prefferd_vars[(day, type_uid)]
            #     * self.instance.shifts[day][type_uid].weight_above_preferred
            # )
        if check == 1:
            print("Genug gut → Suche stoppen.")
            self.StopSearch()
