from pydantic import BaseModel, Field

from . import employee, shift, shiftType


# TODO testen das alle uId sind unique
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
                new_shift = shift.Shift()
                if day in weekend_days:
                    new_shift.is_weekend = True
                self.shifts[day][type.uid] = new_shift

    employees: dict[employee.EmployeeUid, employee.Employee] = Field(
        default_factory=set, description="Set of Employees in the Instance"
    )
    number_of_days: int = Field(
        default=0, description="Number of days in the scheduling Instance"
    )
    # shifts[day][type] = shift
    shifts: dict[int, dict[shiftType.TypeUid, shift.Shift]] = Field(
        default_factory=dict, description="Set of Shifts in the Instance"
    )
    shift_types: dict[shiftType.TypeUid, shiftType.ShiftType] = Field(
        default_factory=dict, description="Set of Shift Types in the Instance"
    )
