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
        for employee_uid in instance.employees:
            for weekend in instance.weekend_days:
                self.weekend_vars[(weekend, employee_uid)] = self.model.new_bool_var(
                    f"weekend_work_{weekend}_for_{employee_uid}"
                )
                for type_uid in instance.shifts[weekend]:
                    # force weekend var for saturday
                    self.model.add(
                        self.weekend_vars[(weekend, employee_uid)]
                        >= self.vars[(weekend, type_uid, employee_uid)]
                    )
                    # force weekend var for sunday
                    if weekend > 0:
                        self.model.add(
                            self.weekend_vars[(weekend, employee_uid)]
                            >= self.vars[(weekend + 1, type_uid, employee_uid)]
                        )

    def get_var(self, day: int, type_uid: int, employee_uid: int):
        return self.vars[(day, type_uid, employee_uid)]

    def get_weekend_var(self, weekend: int, employee_uid: int):
        return self.weekend_vars[(weekend, employee_uid)]
        # TODO y,z variable
