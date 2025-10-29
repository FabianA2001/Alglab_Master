from pydantic import BaseModel, Field

from . import employee, shift, shiftType


class Instance(BaseModel):
    def __init__(
        self,
        number_of_days: int,
        weekend_days: set[int],
        shift_typs: list[shiftType.ShiftType],
        emplyees: list[employee.Employee],
        **data,
    ):
        super().__init__(**data)
        for type in shift_typs:
            self.shift_types[type.uid] = type
        for emp in emplyees:
            self.employees[emp.uid] = emp
        for day in range(number_of_days):
            for type in shift_typs:
                new_shift = shift.Shift(
                    type=type.uid,
                    day=day,
                )
                if day in weekend_days:
                    new_shift.is_weekend = True
                self.shifts[new_shift.uid] = new_shift

    employees: dict[employee.EmployeeUid, employee.Employee] = Field(
        default_factory=set, description="Set of Employees in the Instance"
    )
    number_of_days: int = Field(
        default=0, description="Number of days in the scheduling Instance"
    )
    shifts: dict[shift.ShiftUid, shift.Shift] = Field(
        default_factory=dict, description="Set of Shifts in the Instance"
    )
    shift_types: dict[shiftType.TypeUid, shiftType.ShiftType] = Field(
        default_factory=dict, description="Set of Shift Types in the Instance"
    )

    # days: dict[day.DayUid, day.Day] = Field(
    #     default_factory=dict, description="Set of Days in the scheduling Instance"
    # )
    # weekends: set[day.DayUid] = Field(
    #     default_factory=set, description="Set of weekend Day UIDs in the Instance"
    # )

    # @model_validator(mode="after")
    # def validate_weekends(self):
    #     for dayUid in self.weekends:
    #         assert dayUid in self.days, "Day UIDs must be part of days."
    #         if not self.days[dayUid].is_weekend:
    #             raise ValueError("Day UIDs must be weekend.")
    #     return self
