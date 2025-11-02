from collections import defaultdict

from pydantic import BaseModel, Field, model_validator

from . import employee, shift, shiftType


# TODO testen das alle uId sind unique
class Instance(BaseModel):
    def __init__(
        self,
        number_of_days: int,
        shift_typs: list[shiftType.ShiftType],
        emplyees: list[employee.Employee],
        name: str = "Default Instance",
        # set saturday(Samstag)
        weekend_days: set[int] = set(),
        # (day, shifttype_id) -> (employee_id ->, weight)
        shift_on_requests: dict[tuple[int, int], dict[int, int]] = defaultdict(dict),
        # (day, shifttype_id) -> (employee_id -> weight)
        shift_off_requests: dict[tuple[int, int], dict[int, int]] = defaultdict(dict),
        # (day, shifttype_id) -> (requirement, weight_under, weight_over)
        cover_requirements: dict[tuple[int, int], tuple[int, int, int]] = {},
        **data,
    ):
        # Prepare data dict with all required Pydantic fields
        data["name"] = name
        data["number_of_days"] = number_of_days
        data["weekend_days"] = weekend_days

        super().__init__(**data)

        for type in shift_typs:
            self.shift_types[type.uid] = type
        for emp in emplyees:
            self.employees[emp.uid] = emp
        for day in range(number_of_days):
            for type in shift_typs:
                new_shift = shift.Shift()
                if (day in weekend_days) or (day > 0 and day - 1 in weekend_days):
                    new_shift.is_weekend = True
                new_shift.penalty_assigned_day_employee = shift_on_requests[
                    (day, type.uid)
                ]
                new_shift.penalty_not_assigned_day_employee = shift_off_requests[
                    (day, type.uid)
                ]
                if (day, type.uid) in cover_requirements:
                    cover = cover_requirements[(day, type.uid)]
                    new_shift.preffert_number_employees = cover[0]
                    new_shift.weight_below_preferred = cover[1]
                    new_shift.weight_above_preferred = cover[2]
                self.shifts[day][type.uid] = new_shift

    def __str__(self) -> str:
        result_string = ""
        result_string += f"Instance with {self.number_of_days} days, {len(self.shift_types)} shift types and {len(self.employees)} employees.\n"
        result_string += "\n" * 2
        for shift_type in self.shift_types.values():
            result_string += f"{shift_type}\n"
        result_string += "\n" * 2
        for employee in self.employees.values():
            result_string += f"{employee}\n"
        return result_string

    name: str = Field(description="Name of the Instance")
    employees: dict[employee.EmployeeUid, employee.Employee] = Field(
        default_factory=dict, description="Set of Employees in the Instance"
    )
    number_of_days: int = Field(
        default=0, description="Number of days in the scheduling Instance"
    )
    weekend_days: set[int] = Field(
        default_factory=set,
        description="Set of saturday days in the Instance, does not include sunday",
    )
    # shifts[day][type] = shift
    shifts: dict[int, dict[shiftType.TypeUid, shift.Shift]] = Field(
        default=defaultdict(dict), description="Set of Shifts in the Instance"
    )
    shift_types: dict[shiftType.TypeUid, shiftType.ShiftType] = Field(
        default_factory=dict, description="Set of Shift Types in the Instance"
    )

    def get_shift(self, day: int, type_uid: int) -> shift.Shift:
        return self.shifts[day][type_uid]

    @model_validator(mode="after")
    def validate_nurses_unique_uids(self):
        """Weekends are maximal one consecutive day."""
        for weekend in self.weekend_days:
            if weekend + 1 in self.weekend_days:
                raise ValueError("Weekend days cannot be consecutive.")
        return self
