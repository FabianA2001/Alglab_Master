from ortools.sat.python import cp_model

from .inputTypes import instace


class Shift_vars:
    def __init__(
        self, instance: instace.Instance, model: cp_model.CpModel = cp_model.CpModel()
    ):
        self.model: cp_model.CpModel = model
        # (day, type_uid, employee_uid) -> variable
        self.vars = {}
        for day in range(instance.number_of_days):
            for type_uid in instance.shifts[day]:
                for employee_uid in instance.employees:
                    print("create var")
                    self.vars[(day, type_uid, employee_uid)] = self.model.new_bool_var(
                        f"assign_{day}_{type_uid}_to_{employee_uid}"
                    )

        self.weekend_vars = {}

        # TODO K,y,z variable
