from datetime import datetime

from pydantic import BaseModel, Field

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

    start_time: datetime = Field(
        default=datetime(2005, 1, 1), description="Start time of the Shift"
    )
    end_time: datetime = Field(
        default=datetime(2005, 1, 1), description="End time of the Shift"
    )
