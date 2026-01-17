from ortools.sat.python import cp_model

from .inputTypes import instace


class Shift_vars:
    def __init__(
        self,
        instance: instace.Instance,
        model: cp_model.CpModel | None = None,
    ):
        if model is None:
            self.model = cp_model.CpModel()
        else:
            self.model = model
        #     model: cp_model.CpModel = None,
        # ):
        #     if model is None:
        #         model = cp_model.CpModel()
        #     self.model: cp_model.CpModel = model
        # (day, type_uid, employee_uid) -> variable

        self.__init_vars(instance)
        self.__init_weekend_vars(instance)
        self.__init_below_prefferd_vars(instance)
        self.__init_above_prefferd_vars(instance)
        self.__init_work_vars(instance)
        self.__init_below_threshold_vars(instance)

    def __init_vars(self, instance: instace.Instance):
        self.vars = {}
        for day in range(instance.number_of_days):
            for type_uid in instance.shifts[day]:
                for employee_uid in instance.employees:
                    self.vars[(day, type_uid, employee_uid)] = self.model.new_bool_var(
                        f"assign_{day}_{type_uid}_to_{employee_uid}"
                    )

    def __init_weekend_vars(self, instance: instace.Instance):
        self.weekend_vars = {}
        for employee_uid in instance.employees:
            for weekend in instance.weekend_days:
                self.weekend_vars[(weekend, employee_uid)] = self.model.new_bool_var(
                    f"weekend_work_{weekend}_for_{employee_uid}"
                )

    def __init_below_prefferd_vars(self, instance: instace.Instance):
        self.below_prefferd_vars = {}
        for day in range(instance.number_of_days):
            for type_uid in instance.shifts[day]:
                self.below_prefferd_vars[(day, type_uid)] = self.model.new_int_var(
                    0,
                    instance.get_shift(day, type_uid).preffert_number_employees,
                    f"below_prefferd_{day}_{type_uid}",
                )

    def __init_below_threshold_vars(self, instance: instace.Instance):
        self.below_threshold_vars = {}
        for day in range(instance.number_of_days):
            for type_uid in instance.shifts[day]:
                self.below_threshold_vars[(day, type_uid)] = self.model.new_int_var(
                    0,
                    instance.get_shift(day, type_uid).preffert_number_employees,
                    f"below_threshold_{day}_{type_uid}",
                )

    def __init_above_prefferd_vars(self, instance: instace.Instance):
        number_of_employees = len(instance.employees)
        self.above_prefferd_vars = {}
        for day in range(instance.number_of_days):
            for type_uid in instance.shifts[day]:
                self.above_prefferd_vars[(day, type_uid)] = self.model.new_int_var(
                    0,
                    max(
                        number_of_employees
                        - instance.get_shift(day, type_uid).preffert_number_employees,
                        0,
                    ),
                    f"above_prefferd_{day}_{type_uid}",
                )

    def __init_work_vars(self, instance: instace.Instance):
        self.work_vars = {}

        for employee_uid in instance.employees:
            for day in range(instance.number_of_days):
                # 1) BoolVar erstellen
                w = self.model.new_bool_var(f"work_{day}_for_{employee_uid}")
                self.work_vars[(day, employee_uid)] = w

                # 2) OR/Max über alle shift types dieses Tages
                #    aber: NICHT instance.shift_types – sondern instance.shifts[day]
                #    instance.shift_types sind ALLE shift types global,
                #    instance.shifts[day] sind die shift types, die an diesem Tag vorkommen.
                shift_vars_today = [
                    self.vars[(day, t, employee_uid)]
                    for t in instance.shifts[day]  # <--- WICHTIG: shift types des Tages
                ]

                # Falls der Tag keine Schichten hat → Constraint w == 0
                if len(shift_vars_today) == 0:
                    self.model.Add(w == 0)
                else:
                    self.model.AddMaxEquality(w, shift_vars_today)

    def get_var(self, day: int, type_uid: int, employee_uid: int) -> cp_model.BoolVarT:
        return self.vars[(day, type_uid, employee_uid)]

    def get_weekend_var(self, weekend: int, employee_uid: int) -> cp_model.BoolVarT:
        return self.weekend_vars[(weekend, employee_uid)]

    def get_above_prefferd_var(self, day: int, type_uid: int) -> cp_model.IntVar:
        return self.above_prefferd_vars[(day, type_uid)]

    def get_below_prefferd_var(self, day: int, type_uid: int) -> cp_model.IntVar:
        return self.below_prefferd_vars[(day, type_uid)]

    def get_below_threshold_var(self, day: int, type_uid: int) -> cp_model.IntVar:
        return self.below_threshold_vars[(day, type_uid)]

    def get_work_vars(self, day: int, employee_uid: int) -> cp_model.BoolVarT:
        return self.work_vars[(day, employee_uid)]
