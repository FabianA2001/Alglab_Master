from ortools.sat.python import cp_model

from .. import shift_vars
from ..inputTypes import instace
from .shift_assignment_module import ShiftAssignmentModule


class Limited_shifts_per_type_validation(ShiftAssignmentModule):
    def build(
        self,
        instance: instace.Instance,
        vars: shift_vars.Shift_vars,
    ) -> cp_model.LinearExprT:
        for employee_uid in instance.employees:
            for type_uid in instance.shift_types:
                assigned_shifts = []
                for day in range(instance.number_of_days):
                    assigned_shifts.append(vars.vars[(day, type_uid, employee_uid)])
                vars.model.add(
                    sum(assigned_shifts)
                    <= instance.employees[employee_uid].max_numbers_of_shifts[type_uid]
                )
                vars.add_active_constraint(
                    f"limit_shift_{type_uid}_for_{employee_uid}",
                    sum(assigned_shifts)
                    <= instance.employees[employee_uid].max_numbers_of_shifts[type_uid],
                )
        return 0
