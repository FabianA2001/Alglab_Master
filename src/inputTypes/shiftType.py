from pydantic import BaseModel, Field

from . import day
from .inputTypesUtiles import generate_random_uid

# Semantic type aliases for clarity
TypeUid = int


class ShiftType(BaseModel):
    uid: TypeUid = Field(
        default_factory=generate_random_uid,
        description="Unique identifier for the Shift Type",
    )
    name: str = Field(default_factory=str, description="Name of the Shift Type")
    length: int = Field(default=0, description="Length of the Shift Type in minutes")
    blocked_shifts_after: set[TypeUid] = Field(
        default_factory=set,
        description="List of blocked shift UIDs after this Shift Type",
    )
    prefert_number_employees: set[day.DayUid] = Field(
        default_factory=set,
        description="Preferred number of employees for this Shift Type",
    )
    weight_below_preferred_per_day: set[day.DayUid] = Field(
        default_factory=set,
        description="Weight for being below the preferred number of employees per day",
    )
    weight_above_preferred_per_day: set[day.DayUid] = Field(
        default_factory=set,
        description="Weight for being above the preferred number of employees per day",
    )
