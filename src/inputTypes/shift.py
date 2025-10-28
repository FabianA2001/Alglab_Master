from datetime import datetime

from pydantic import BaseModel, Field

from . import day, employee, shiftType
from .inputTypesUtiles import generate_random_uid

# Semantic type aliases for clarity
ShiftUid = int


class Employee(BaseModel):
    uid: ShiftUid = Field(
        default_factory=generate_random_uid,
        description="Unique identifier for the Shift",
    )
    type: shiftType.TypeUid = Field(..., description="Type UID of the Shift")
    name: str = Field(default_factory=str, description="Name of the Shift")
    start_time: datetime = Field(
        default=datetime(2005, 1, 1), description="Start time of the Shift"
    )
    end_time: datetime = Field(
        default=datetime(2005, 1, 1), description="End time of the Shift"
    )
    penalty_not_assigned_day_employee: set[day.DayUid] = Field(
        default_factory=set[employee.EmployeeUid],
        description="Set of penalties for not assigning the shift to an employee on a specific day",
    )
    penalty_assigned_day_employee: set[day.DayUid] = Field(
        default_factory=set[employee.EmployeeUid],
        description="Set of penalties for assigning the shift to an employee on a specific day",
    )
