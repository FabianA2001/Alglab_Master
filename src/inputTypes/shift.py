from datetime import datetime

from pydantic import BaseModel, Field

from . import employee, shiftType
from .inputTypesUtiles import generate_random_uid

# Semantic type aliases for clarity
ShiftUid = int


class Shift(BaseModel):
    uid: ShiftUid = Field(
        default_factory=generate_random_uid,
        description="Unique identifier for the Shift",
    )
    type: shiftType.TypeUid = Field(..., description="Type UID of the Shift")
    day: int = Field(..., description="Day UID of the Shift")
    name: str = Field(default_factory=str, description="Name of the Shift")
    start_time: datetime = Field(
        default=datetime(2005, 1, 1), description="Start time of the Shift"
    )
    end_time: datetime = Field(
        default=datetime(2005, 1, 1), description="End time of the Shift"
    )
    is_weekend: bool = Field(
        default=False, description="Indicates if the Day is a weekend"
    )
    penalty_not_assigned_day_employee: set[employee.EmployeeUid] = Field(
        default_factory=set,
        description="Set of penalties for not assigning the shift to an employee",
    )
    penalty_assigned_day_employee: set[employee.EmployeeUid] = Field(
        default_factory=set,
        description="Set of penalties for assigning the shift to an employee",
    )
