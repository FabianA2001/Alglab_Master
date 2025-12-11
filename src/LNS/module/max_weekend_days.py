from ortools.sat.python import cp_model

from ... import shift_vars
from ...inputTypes import instace
from ...module.shift_assignment_module import ShiftAssignmentModule

# wekkend vars gegebenfalls noch nicht korrekt


class Max_weekend_days(ShiftAssignmentModule):
    def __init__(
        self,
        start_day: int,
    ):
        self.start_day: int = start_day
        super().__init__()

    def build(
        self,
        instance: instace.Instance,
        vars: shift_vars.Shift_vars,
    ) -> cp_model.LinearExprT:
        for employee_uid in instance.employees:
            assigned_weekends = []
            for weekend in range(round(instance.number_of_days / 7)):
                assigned_shifts = []
                day = 7 * (weekend + 1) - 1
                for type_uid in instance.shifts[weekend]:
                    # + 1 because of for range start with 0, - 1 because are weekends days are on 5 and 6
                    # not 6 and 7
                    assigned_shifts.append(vars.vars[(day - 1, type_uid, employee_uid)])
                    assigned_shifts.append(vars.vars[(day, type_uid, employee_uid)])

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
