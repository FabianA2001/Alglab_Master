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
            assigned_weekends = []
            for weekend in instance.weekend_days:
                assigned_shifts = []
                for type_uid in instance.shifts[weekend]:
                    if weekend > 0:
                        assigned_shifts.append(
                            # + 1 because of for range start with 0, - 1 because are weekends days are on 5 and 6
                            # not 6 and 7
                            vars.vars[((weekend - 1), type_uid, employee_uid)]
                        )
                    assigned_shifts.append(vars.vars[(weekend, type_uid, employee_uid)])

                vars.model.Add(
                    vars.weekend_vars[(weekend, employee_uid)] <= sum(assigned_shifts)
                )
                vars.model.Add(
                    # x
                    sum(assigned_shifts)
                    <= 2 * (vars.weekend_vars[(weekend, employee_uid)])
                )
                assigned_weekends.append(vars.weekend_vars[(weekend, employee_uid)])
            vars.model.Add(
                sum(assigned_weekends)
                <= instance.employees[employee_uid].max_number_weekends
            )
        return 0
