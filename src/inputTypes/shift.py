from collections import defaultdict

from pydantic import BaseModel, Field

from . import employee
from .inputTypesUtiles import generate_random_uid

# Semantic type aliases for clarity
ShiftUid = int


class Shift(BaseModel):
    uid: ShiftUid = Field(
        default_factory=generate_random_uid,
        description="Unique identifier for the Shift",
    )
    name: str = Field(default_factory=str, description="Name of the Shift")

    is_weekend: bool = Field(
        default=False, description="Indicates if the Day is a weekend"
    )
    penalty_not_assigned_day_employee: dict[employee.EmployeeUid, int] = Field(
        default=defaultdict(int),
        description="dict of penalty for employee being assigned on specific day",
    )
    assign_employee_day_shift: set[employee.EmployeeUid] = Field(
        default_factory=set,
        description="Assign Employee from the shift on this day",
    )
    ban_employee_day_shift: set[employee.EmployeeUid] = Field(
        default_factory=set,
        description="Ban Employee from the shift on this day",
    )
    penalty_assigned_day_employee: dict[employee.EmployeeUid, int] = Field(
        default=defaultdict(int),
        description="dict of penalty for employee not being assigned on specific day",
    )
    preffert_number_employees: int = Field(
        default=0,
        description="Preferred number of employees for this Shift",
    )
    weight_below_preferred: int = Field(
        default=0,
        description="Weight for being below the preferred number of employees",
    )
    weight_above_preferred: int = Field(
        default=0,
        description="Weight for being above the preferred number of employees",
    )
