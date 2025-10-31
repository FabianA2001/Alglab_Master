from typing import Dict, Tuple

from pydantic import BaseModel, Field

from .inputTypes import employee, instace, shift


class Solution(BaseModel):
    def __init__(self, instance: instace.Instance, **data):
        super().__init__(instance=instance, **data)

    """Class to handle variable storage and management for shift scheduling."""

    vars: Dict[Tuple[int, shift.ShiftUid, employee.EmployeeUid], int] = Field(
        default_factory=dict,
        description="Mapping of boolean variables that indicate whether a specific employee is assigned to a given shift on a specified day. The key is a tuple of (day, shift type, employee ID).",
    )

    weekend_vars: Dict[Tuple[int, employee.EmployeeUid], int] = Field(
        default_factory=dict,
        description="Mapping of boolean variables that indicate whether a specific employee is working on a weekend day. The key is a tuple of (weekend day, employee ID).",
    )

    above_prefferd_vars: Dict[Tuple[int, shift.ShiftUid], int] = Field(
        default_factory=dict,
        description="Mapping of integer variables representing the excess number of employees assigned to a shift above its preferred capacity. The key is a tuple of (day, shift type).",
    )

    below_prefferd_vars: Dict[Tuple[int, shift.ShiftUid], int] = Field(
        default_factory=dict,
        description="Mapping of integer variables representing the shortfall of employees assigned to a shift below its preferred capacity. The key is a tuple of (day, shift type).",
    )
    instance: instace.Instance = Field(
        description="An instance that contains all given variables",
    )
    objective_value: float = Field(
        default=0.0,
        description="The result of an objective function",
    )

    def set_var(self, day: int, type_uid: int, employee_uid: int, value: int):
        """Sets the boolean variable value."""
        self.vars[(day, type_uid, employee_uid)] = value

    def set_weekend_var(self, weekend: int, employee_uid: int, value: int):
        """Sets the weekend variable value."""
        self.weekend_vars[(weekend, employee_uid)] = value

    def set_above_prefferd_var(self, day: int, type_uid: int, value: int):
        """Sets the above preferred variable value."""
        self.above_prefferd_vars[(day, type_uid)] = value

    def set_below_prefferd_var(self, day: int, type_uid: int, value: int):
        """Sets the below preferred variable value."""
        self.below_prefferd_vars[(day, type_uid)] = value

    def set_instance(self, instance: instace.Instance):
        self.instance = instance

    def set_objective_value(self, objective_value: float):
        self.objective_value = objective_value

    def print_assign(self):
        for day, type_uid, employee_uid in self.vars.keys():
            print(
                f"assign_{day}_{type_uid}_to_{employee_uid}: ",
                self.vars[(day, type_uid, employee_uid)],
            )

    def print_weekend_work(self):
        for weekend, employee_uid in self.weekend_vars.keys():
            print(
                f"weekend_work_{weekend}_for_{employee_uid}: ",
                self.weekend_vars[(weekend, employee_uid)],
            )

    def print_below_prefferd(self):
        for day, type_uid in self.below_prefferd_vars.keys():
            print(
                f"below_prefferd_{day}_{type_uid}: ",
                self.below_prefferd_vars[(day, type_uid)],
            )

    def print_assign_above_prefferd(self):
        for day, type_uid in self.above_prefferd_vars.keys():
            print(
                f"below_prefferd_{day}_{type_uid}: ",
                self.above_prefferd_vars[(day, type_uid)],
            )

    def print_all_variables(self):
        self.print_assign()
        print("\n" * 2)
        self.print_weekend_work()
        print("\n" * 2)
        self.print_below_prefferd()
        print("\n" * 2)
        self.print_assign_above_prefferd()
