import math

from pydantic import BaseModel, Field

from . import shiftType
from .inputTypesUtiles import generate_random_uid

# Semantic type aliases for clarity
EmployeeUid = int


class Employee(BaseModel):
    uid: EmployeeUid = Field(
        default_factory=generate_random_uid,
        description="Unique identifier for the Employee",
    )
    name: str = Field(default_factory=str, description="Name of the Employee")
    blocked_shifts: set[EmployeeUid] = Field(
        default_factory=set, description="List of blocked shift UIDs for the Employee"
    )
    max_numbers_of_shifts: dict[shiftType.TypeUid, int] = Field(
        default_factory=dict,
        description="Set of maximum number of shifts per shift type for the Employee",
    )
    min_minutes_assigned: int = Field(
        default=0, description="Minimum number of minutes assigned to the Employee"
    )
    max_minutes_assigned: int = Field(
        default=math.inf,
        description="Maximum number of minutes assigned to the Employee",
    )
    min_number_consecutive_shifts: int = Field(
        default=0,
        description="Minimum number of consecutive shifts for the Employee",
    )
    max_number_consecutive_shifts: int = Field(
        default=math.inf,
        description="Maximum number of consecutive shifts for the Employee",
    )
    max_number_weekends: int = Field(
        default=math.inf, description="Maximum number of weekends for the Employee"
    )
