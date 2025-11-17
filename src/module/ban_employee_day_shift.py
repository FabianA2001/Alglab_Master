from ortools.sat.python import cp_model

from .. import shift_vars
from ..inputTypes import instace
from .shift_assignment_module import ShiftAssignmentModule


class Ban_employee_day_shift(ShiftAssignmentModule):
    def build(
        self,
        instance: instace.Instance,
        vars: shift_vars.Shift_vars,
    ) -> cp_model.LinearExprT:
        for day in range(instance.number_of_days):
            for type_uid in instance.shifts[day]:
                for employee_uid in instance.shifts[day][
                    type_uid
                ].ban_employee_day_shift:
                    print("ban employee", employee_uid)
                    vars.model.Add(vars.get_var(day, type_uid, employee_uid) == 0)
                    print(" employee banned")
        return 0
