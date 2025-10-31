from typing import Dict, Tuple

from pydantic import BaseModel, Field

from .inputTypes import employee, instace, shift
from .inputTypes.instace import Instance


class Solution(BaseModel):
    def __init__(self, instance: Instance):
        self.instance = instance

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
        default_factory=float,
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
