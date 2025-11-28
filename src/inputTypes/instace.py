from collections import defaultdict

from pydantic import BaseModel, Field, model_validator

from . import employee, shift, shiftType


# TODO testen das alle uId sind unique
class Instance(BaseModel):
    @classmethod
    def create(
        cls,
        number_of_days: int,
        shift_typs: list[shiftType.ShiftType],
        emplyees: list[employee.Employee],
        name: str = "Default Instance",
        # set saturday(Samstag)
        weekend_days: set[int] | None = None,
        # (day, shifttype_id) -> (employee_id ->, weight)
        shift_on_requests: dict[tuple[int, int], dict[int, int]] | None = None,
        # (day, shifttype_id) -> (employee_id -> weight)
        shift_off_requests: dict[tuple[int, int], dict[int, int]] | None = None,
        # (day, shifttype_id) -> (preffert_number_employees, weight_under, weight_over)
        cover_requirements: dict[tuple[int, int], tuple[int, int, int]] | None = None,
    ) -> "Instance":
        """
        Create a new Instance with all shifts and employees configured.

        Args:
            number_of_days: Number of days in the scheduling period
            shift_typs: List of shift types
            emplyees: List of employees
            name: Name of the instance
            weekend_days: Set of saturday days (not including sunday)
            shift_on_requests: Preferences for being assigned to shifts
            shift_off_requests: Preferences for not being assigned to shifts
            cover_requirements: Required coverage for each shift

        Returns:
            A fully configured Instance object
        """
        # Handle mutable default arguments
        if weekend_days is None:
            weekend_days = set()
        if shift_on_requests is None:
            shift_on_requests = defaultdict(dict)
        if shift_off_requests is None:
            shift_off_requests = defaultdict(dict)
        if cover_requirements is None:
            cover_requirements = {}

        # Build the employees and shift_types dictionaries
        employees_dict = {emp.uid: emp for emp in emplyees}
        shift_types_dict = {type.uid: type for type in shift_typs}

        # Build all shifts
        shifts_dict = defaultdict(dict)
        for day in range(number_of_days):
            for type in shift_typs:
                new_shift = shift.Shift()
                if (day in weekend_days) or (day > 0 and day - 1 in weekend_days):
                    new_shift.is_weekend = True
                new_shift.penalty_not_assigned_day_employee = shift_on_requests.get(
                    (day, type.uid), {}
                )
                new_shift.penalty_assigned_day_employee = shift_off_requests.get(
                    (day, type.uid), {}
                )
                if (day, type.uid) in cover_requirements:
                    cover = cover_requirements[(day, type.uid)]
                    new_shift.preffert_number_employees = cover[0]
                    new_shift.weight_below_preferred = cover[1]
                    new_shift.weight_above_preferred = cover[2]
                shifts_dict[day][type.uid] = new_shift

        # Create the instance using Pydantic's normal initialization
        return cls(
            name=name,
            number_of_days=number_of_days,
            weekend_days=weekend_days,
            employees=employees_dict,
            shift_types=shift_types_dict,
            shifts=shifts_dict,
        )

    def __str__(self) -> str:
        result_string = ""
        result_string += f"Instance with {self.number_of_days} days, {len(self.shift_types)} shift types and {len(self.employees)} employees.\n"
        result_string += "\n" * 2
        for shift_type in self.shift_types.values():
            result_string += f"{shift_type}\n"
        result_string += "\n" * 2
        for emp in self.employees.values():
            result_string += f"{emp}\n"
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
