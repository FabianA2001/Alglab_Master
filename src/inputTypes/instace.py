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
            # add all sundays as weekend days by default
            weekend_days = set(((i + 1) * 7) - 1 for i in range(number_of_days // 7))
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
                new_shift.penalty_assigned_day_employee = shift_on_requests.get(
                    (day, type.uid), {}
                )
                new_shift.penalty_not_assigned_day_employee = shift_off_requests.get(
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
        description="Set of sunday days in the Instance",
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
            if weekend > 0 and weekend - 1 in self.weekend_days:
                raise ValueError("Weekend days cannot be consecutive.")
        return self
    
    # 4, 5, 6, 7, 8, 9, 10
    #TODO I think i did not consider ban and other stuff
    def instance_to_one_shift_type(self):
        from ..help_functions import hash_string
        # number_of_days: int,
        instance_copy = self.model_copy(deep=True)
        number_of_days = instance_copy.number_of_days + 0

        # shift_typs: list[shiftType.ShiftType],
        counter = 0
        length = 0
        shift_name = "all"
        for shift_type_uid, shift_type in instance_copy.shift_types.items():
            counter = counter + 1
            length = length + shift_type.length
        shift_types_new = [shiftType.ShiftType(
                    uid=hash_string(shift_name),
                    length=int(length/counter),
                    name=shift_name,
                )]
        
        employees: list[employee.Employee] = []
        for employee_uid, employee_ in instance_copy.employees.items():
            employees.append(employee_.model_copy())

        for employee_ in employees:
            employee_.max_numbers_of_shifts = {hash_string("all"): 999999}
        instance_name = instance_copy.name+""

        shift_on_requests: dict[tuple[int, int], dict[int, int]] = defaultdict(dict)
        shift_off_requests: dict[tuple[int, int], dict[int, int]] = defaultdict(dict)
        for day in range(instance_copy.number_of_days):
            for shift_type_uid, shift_type in instance_copy.shift_types.items():
                for employee_uid, employee_ in instance_copy.employees.items():
                    if employee_uid in instance_copy.shifts[day][shift_type_uid].penalty_assigned_day_employee.keys():
                        # TODO this might be problimatic because one day might have bad and good shifts for an employee
                        shift_on_requests[(day, hash_string("all"))][
                            employee_uid
                        ] = instance_copy.shifts[day][shift_type_uid].penalty_assigned_day_employee[employee_uid]
                    if employee_uid in instance_copy.shifts[day][shift_type_uid].penalty_not_assigned_day_employee.keys():
                        shift_off_requests[(day, hash_string("all"))][
                            employee_uid
                        ] = instance_copy.shifts[day][shift_type_uid].penalty_not_assigned_day_employee[employee_uid]

        cover_requirements: dict[tuple[int, int], tuple[int, int, int]] = {}

        for day in range(instance_copy.number_of_days):
            for shift_type_uid, shift_type in instance_copy.shift_types.items():
                if (day, hash_string("all")) in cover_requirements:
                    cover_requirements[(day, hash_string("all"))] = (
                        instance_copy.shifts[day][shift_type_uid].preffert_number_employees+cover_requirements[(day, hash_string("all"))][0],
                        instance_copy.shifts[day][shift_type_uid].weight_below_preferred+cover_requirements[(day, hash_string("all"))][1],
                        instance_copy.shifts[day][shift_type_uid].weight_above_preferred+cover_requirements[(day, hash_string("all"))][2]
                    )
                else:
                    cover_requirements[(day, hash_string("all"))] = (
                        instance_copy.shifts[day][shift_type_uid].preffert_number_employees,
                        instance_copy.shifts[day][shift_type_uid].weight_below_preferred,
                        instance_copy.shifts[day][shift_type_uid].weight_above_preferred
                    )
        #TODO another better way is to have multiple shifts, each shift correspond to its own employee group.
        # shift_balance_dict: dict[shiftType.TypeUid, int] = {}
        # for shift_uid, shift_type in self.shift_types.items():
        #     shift_balance_dict[shift_uid]=0

        # for employee_ in self.employees.values():
        #     for shift_uid, number_of_shifts in employee_.max_numbers_of_shifts.items():
        #         if number_of_shifts > 0:
        #             shift_balance_dict[shift_uid]=shift_balance_dict[shift_uid]+1

        # shift_length=0
        # for shift_uid, shift_type in self.shift_types.items():
        #     shift_length=shift_length+shift_balance_dict[shift_uid]*shift_type.length
        # shift_length=shift_length/sum(shift_balance_dict.values())

        # shift_types_new[0].length=int(shift_length)
        # print(int(shift_length))

        return Instance.create(
            name=instance_name,
            number_of_days=number_of_days,
            shift_typs=shift_types_new,
            emplyees=employees,
            shift_on_requests=shift_on_requests,
            shift_off_requests=shift_off_requests,
            cover_requirements=cover_requirements,
        )