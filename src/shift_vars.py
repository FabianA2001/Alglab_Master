from ortools.sat.python import cp_model

from .inputTypes import instace


class Shift_vars:
    def __init__(
        self,
        instance: instace.Instance,
        model: cp_model.CpModel = cp_model.CpModel(),
    ):
        self.model: cp_model.CpModel = model
        # (day, type_uid, employee_uid) -> variable

        self.__init_vars(instance)
        self.__init_weekend_vars(instance)
        self.__init_below_prefferd_vars(instance)
        self.__init_above_prefferd_vars(instance)
        self.__init_work_vars(instance)
        self.__init_below_threshold_vars(instance)
        # self.__init_free_days_in_interval(instance)
        # self.__init_free_days_on_sides(instance)
        # self.__init_work_days_in_interval(instance)
        # self.__init_work_days_on_sides(instance)

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
            for weekend in range(round(instance.number_of_days / 7)):
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
    
    def get_work_vars(self, day: int, employee_uid: int) -> cp_model.BoolVarT:
        return self.work_vars[(day, employee_uid)]
    




    # def __init_free_days_on_sides(self, instance: instace.Instance):
    #     """
    #     Define variables that need to be used in consecutive shifts to decide if the constraint
    #     should be considered or not. The constraint should be considered if this variable is 
    #     true. This variable is true if the two days - the day before the consecutive shift interval
    #     and the day after the consecutive shift interval - are free days.
        
    #     :param self: Description
    #     :param instance: Description
    #     :type instance: instace.Instance
    #     """
    #     self.free_days_on_sides = {}
    #     for day in range(instance.number_of_days):
    #             for employee_uid in instance.employees:
    #                 self.free_days_on_sides[(day, employee_uid)] = self.model.new_bool_var(
    #                     f"free_days_on_sides_{day}_{employee_uid}"
    #                 )


    # def __init_work_days_in_interval(self, instance: instace.Instance):
    #     """
    #     Define variables that need to be used in consecutive shifts to decide if the constraint
    #     should be considered or not. The constraint should be considered if this variable is 
    #     true. This variable is true if their is a working day in a consecutive shift interval.
        
    #     :param self: Description
    #     :param instance: Description
    #     :type instance: instace.Instance
    #     """
    #     self.work_days_in_interval = {}
    #     for day in range(instance.number_of_days):
    #             for employee_uid in instance.employees:
    #                 self.work_days_in_interval[(day, employee_uid)] = self.model.new_bool_var(
    #                     f"work_days_in_interval_{day}_{employee_uid}"
    #                 )

    # def __init_work_days_on_sides(self, instance: instace.Instance):
    #     """
    #     Define variables that need to be used in consecutive free shifts to decide if the constraint
    #     should be considered or not. The constraint should be considered if this variable is 
    #     true. This variable is true if the two days - the day before the consecutive free shift interval
    #     and the day after the consecutive free shift interval - are work days.
        
    #     :param self: Description
    #     :param instance: Description
    #     :type instance: instace.Instance
    #     """
    #     self.work_days_on_sides = {}
    #     for day in range(instance.number_of_days):
    #             for employee_uid in instance.employees:
    #                 self.work_days_on_sides[(day, employee_uid)] = self.model.new_bool_var(
    #                     f"work_days_on_sides_{day}_{employee_uid}"
    #                 )

    # def __init_free_days_in_interval(self, instance: instace.Instance):
    #     """
    #     Define variables that need to be used in consecutive free shifts to decide if the constraint
    #     should be considered or not. The constraint should be considered if this variable is 
    #     true. This variable is true if their is a free day in a consecutive free shift interval.
        
    #     :param self: Description
    #     :param instance: Description
    #     :type instance: instace.Instance
    #     """
    #     self.free_days_in_interval = {}
    #     for day in range(instance.number_of_days):
    #             for employee_uid in instance.employees:
    #                 self.free_days_in_interval[(day, employee_uid)] = self.model.new_bool_var(
    #                     f"free_days_in_interval_{day}_{employee_uid}"
    #                 )

 
    # def get_free_days_on_sides(self, day: int, employee_uid: int) -> cp_model.BoolVarT:
    #     return self.free_days_on_sides[(day, employee_uid)]
    
    # def get_work_days_in_interval(self, day: int, employee_uid: int) -> cp_model.BoolVarT:
    #     return self.work_days_in_interval[(day, employee_uid)]
    
    # def get_work_days_on_sides(self, day: int, employee_uid: int) -> cp_model.BoolVarT:
    #     return self.work_days_on_sides[(day, employee_uid)]
    
    # def get_free_days_in_interval(self, day: int, employee_uid: int) -> cp_model.BoolVarT:
    #     return self.free_days_in_interval[(day, employee_uid)]