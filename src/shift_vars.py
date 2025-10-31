from typing import Union
from ortools.sat.python import cp_model

from .inputTypes import instace
from ortools.sat.python.cp_model_helper import BoundedLinearExpression


class Shift_vars:
    def __init__(
        self,
        instance: instace.Instance,
        model: cp_model.CpModel = cp_model.CpModel(),
        active_constraints: dict[str, BoundedLinearExpression] = {},
        deactivate_constraints: dict[str, BoundedLinearExpression] = {},
    ):
        self.model: cp_model.CpModel = model
        self.active_constraints = active_constraints
        self.deactivate_constraints = deactivate_constraints
        # (day, type_uid, employee_uid) -> variable

        self.__init_vars(instance)
        self.__init_weekend_vars(instance)
        self.__init_below_prefferd_vars(instance)
        self.__init_above_prefferd_vars(instance)

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
                # for type_uid in instance.shifts[weekend]:
                #     # force weekend var for saturday
                #     self.model.add(
                #         self.weekend_vars[(weekend, employee_uid)]
                #         >= self.vars[(weekend, type_uid, employee_uid)]
                #     )
                #     # force weekend var for sunday
                #     if weekend > 0:
                #         self.model.add(
                #             self.weekend_vars[(weekend, employee_uid)]
                #             >= self.vars[(weekend + 1, type_uid, employee_uid)]
                #         )

    def __init_below_prefferd_vars(self, instance: instace.Instance):
        self.below_prefferd_vars = {}
        for day in range(instance.number_of_days):
            for type_uid in instance.shifts[day]:
                self.below_prefferd_vars[(day, type_uid)] = self.model.new_int_var(
                    0,
                    instance.get_shift(day, type_uid).preffert_number_employees,
                    f"below_prefferd_{day}_{type_uid}",
                )
                self.model.add(
                    instance.get_shift(day, type_uid).preffert_number_employees
                    - sum(
                        self.vars[(day, type_uid, emp_uid)]
                        for emp_uid in instance.employees
                    )
                    <= self.below_prefferd_vars[(day, type_uid)]
                )
                self.model.add(self.below_prefferd_vars[(day, type_uid)] >= 0)

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
                self.model.add(
                    sum(
                        self.vars[(day, type_uid, emp_uid)]
                        for emp_uid in instance.employees
                    )
                    - instance.get_shift(day, type_uid).preffert_number_employees
                    <= self.above_prefferd_vars[(day, type_uid)]
                )
                self.model.add(self.above_prefferd_vars[(day, type_uid)] >= 0)

    def add_active_constraint(
        self, key: str, constraint: Union[BoundedLinearExpression, bool]
    ):
        if isinstance(constraint, BoundedLinearExpression):
            self.active_constraints[key] = constraint
        else:
            raise TypeError("Constraint must be of type BoundedLinearExpression.")

    def add_deactive_constraint(
        self, key: str, constraint: Union[BoundedLinearExpression, bool]
    ):
        if isinstance(constraint, BoundedLinearExpression):
            self.deactivate_constraints[key] = constraint
        else:
            raise TypeError("Constraint must be of type BoundedLinearExpression.")

    def activate_constraint(self, key: str):
        if key in self.deactivate_constraints:
            value = self.deactivate_constraints.pop(key)
            self.active_constraints[key] = value
            return value

    def deactivate_constraint(self, key: str):
        if key in self.active_constraints:
            value = self.active_constraints.pop(key)
            self.deactivate_constraints[key] = value
            return value

    def get_var(self, day: int, type_uid: int, employee_uid: int) -> cp_model.BoolVarT:
        return self.vars[(day, type_uid, employee_uid)]

    def get_weekend_var(self, weekend: int, employee_uid: int) -> cp_model.BoolVarT:
        return self.weekend_vars[(weekend, employee_uid)]

    def get_above_prefferd_var(self, day: int, type_uid: int) -> cp_model.IntVar:
        return self.above_prefferd_vars[(day, type_uid)]

    def get_below_prefferd_var(self, day: int, type_uid: int) -> cp_model.IntVar:
        return self.below_prefferd_vars[(day, type_uid)]
