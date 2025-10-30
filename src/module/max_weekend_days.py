from ortools.sat.python import cp_model

from .. import shift_vars
from ..inputTypes import instace
from .shift_assignment_module import ShiftAssignmentModule

# wekkend vars gegebenfalls noch nicht korrekt


class Max_weekend_days(ShiftAssignmentModule):
    def build(
        self,
        instance: instace.Instance,
        vars: shift_vars.Shift_vars,

    ) -> cp_model.LinearExprT:
        for employee_uid in instance.employees:

            for day in range(instance.weekend_days):
                assigned_shifts = []
                for type_uid in instance.shifts[day]:
                    assigned_shifts.append(
                        vars.vars[((7*day-1), type_uid, employee_uid)])
                    assigned_shifts.append(
                        vars.vars[((7*day), type_uid, employee_uid)])

                vars.model.Add(vars.weekend_vars[day][employee_uid] <= sum(
                    assigned_shifts) <= 2*(vars.weekend_vars[day][employee_uid]))
            vars.model.Add(sum(vars.weekend_vars[day][employee_uid])
                           <= instance.employees[employee_uid].max_number_weekends)
        return 0
