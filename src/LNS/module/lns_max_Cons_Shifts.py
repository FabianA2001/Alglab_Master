from ortools.sat.python import cp_model

from ... import shift_vars
from ...inputTypes import instace
from ...inputTypes.employee import EmployeeUid
from ...module.shift_assignment_module import ShiftAssignmentModule


class LNS_Max_Cons_Shifts(ShiftAssignmentModule):
    def __init__(self, config: dict[EmployeeUid, tuple[int, int]]):
        # employeeUID : (max_start, max_end)
        self.config = config
        super().__init__()

    def build(
        self,
        instance: instace.Instance,
        vars: shift_vars.Shift_vars,
    ) -> cp_model.LinearExprT:
        for employee_uid in instance.employees:
            emp_bounds = self.config.get(employee_uid)
            window_size = (
                instance.employees[employee_uid].max_number_consecutive_shifts + 1
            )
            # iterate over possible window starts (as before)
            for day in range(
                instance.number_of_days
                - instance.employees[employee_uid].max_number_consecutive_shifts
            ):
                window_start = day
                window_end = day + window_size - 1

                # If this employee has a per-employee config entry, read it and
                # skip windows that overlap the first `max_start` days or the
                # last `max_end` days for that employee. If no config is set
                # for the employee, apply the constraint normally.
                if emp_bounds is not None:
                    emp_max_start, emp_max_end = emp_bounds
                    if (
                        window_start < emp_max_start
                        or window_end >= instance.number_of_days - emp_max_end
                    ):
                        continue

                assigned_shifts = []
                for type_uid in instance.shifts[day]:
                    for i in range(window_size):
                        assigned_shifts.append(
                            vars.vars[(day + i, type_uid, employee_uid)]
                        )

                vars.model.Add(
                    sum(assigned_shifts)
                    <= instance.employees[employee_uid].max_number_consecutive_shifts
                )
        return 0
