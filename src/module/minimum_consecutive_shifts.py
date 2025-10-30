from ortools.sat.python import cp_model

from .. import shift_vars
from ..inputTypes import instace
from .shift_assignment_module import ShiftAssignmentModule


class Minimum_consecutive_shifts(ShiftAssignmentModule):
    def build(
        self,
        instance: instace.Instance,
        vars: shift_vars.Shift_vars,
    ) -> cp_model.LinearExprT:
        for employee_uid in instance.employees:
            for day_s in range(
                instance.employees[employee_uid].min_number_consecutive_shifts - 1
            ):
                for day_d in range(instance.number_of_days - (day_s + 1) - 1):
                    assigned_shifts = []
                    assigned_shifts_inner_interval = []
                    assigned_shifts_interval_end = []
                    for type_uid in instance.shift_types:
                        assigned_shifts.append(
                            vars.vars[(day_d, type_uid, employee_uid)]
                        )
                        # Because range end range is exclusive, the end range should have + 1
                        # Because day_s start with 0, another +1 should be added
                        for day_j in range(day_d + 1, day_d + day_s + 1 + 1):
                            assigned_shifts_inner_interval.append(
                                vars.vars[(day_j, type_uid, employee_uid)]
                            )
                        assigned_shifts_interval_end.append(
                            vars.vars[(day_d + day_s + 1 + 1, type_uid, employee_uid)]
                        )
                    # Even though our indecies start with 0, day_s should still have the start value of 1
                    vars.model.add(
                        sum(assigned_shifts)
                        + day_s
                        + 1
                        - (sum(assigned_shifts_inner_interval))
                        + sum(assigned_shifts_interval_end)
                        > 0
                    )
        return 0
