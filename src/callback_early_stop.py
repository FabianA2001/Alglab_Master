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


class Callback_Early_Stop(cp_model.CpSolverSolutionCallback):
    def __init__(self, instance: instace.Instance, vars: shift_vars.Shift_vars):
        super().__init__()
        self.instance = instance
        self.vars = vars
        self.solve_time = 0
        self.start_solve_time: datetime = datetime(2005, 1, 1, 0, 0)
        self.ratio_wishes = 0.8
        self.reatio_below_pref = 0.5

    def on_solution_callback(self):
        total_weights = 0
        satisfied_wishes = 0

        # Über alle Schichten der Instanz iterieren
        for day, day_shift_dict in self.instance.shifts.items():
            for type_uid, shift in day_shift_dict.items():
                # Beispiel: preferred employees check
                pref = shift.preffert_number_employees

                below = self.Value(self.vars.below_prefferd_vars[(day, type_uid)])
                if below > pref * self.reatio_below_pref:
                    return  # schlechte Lösung -> sofort abbrechen

                # Wünsche
                for emp in self.instance.employees:
                    weight_pos = shift.penalty_assigned_day_employee.get(emp, 0)
                    weight_neg = shift.penalty_not_assigned_day_employee.get(emp, 0)

                    if weight_pos > 0:
                        total_weights += 1
                        if self.Value(self.vars.vars[(day, type_uid, emp)]) == 1:
                            satisfied_wishes += 1

                    if weight_neg > 0:
                        total_weights += 1
                        if self.Value(self.vars.vars[(day, type_uid, emp)]) == 0:
                            satisfied_wishes += 1

        if total_weights == 0:
            return

        ratio = satisfied_wishes / total_weights

        if ratio >= self.ratio_wishes:
            print("Gute Lösung -> StopSearch()")
            self.StopSearch()