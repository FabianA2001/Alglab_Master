from pydantic import BaseModel, Field

from .inputTypesUtiles import generate_random_uid

# Semantic type aliases for clarity
DayUid = int


class Day(BaseModel):
    uid: DayUid = Field(
        default_factory=generate_random_uid,
        description="Unique identifier for the Day",
    )
    name: str = Field(default_factory=str, description="Name of the Day")
    isWeekend: bool = Field(
        default=False, description="Indicates if the Day is a weekend"
    )
