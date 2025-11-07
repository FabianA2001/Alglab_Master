from collections import defaultdict

from pydantic import BaseModel, Field, model_validator

from ...inputTypes import employee, shift, shiftType, instace


def create_new_instance(
    instance: instace.Instance,
    name: str = "Default Instance",
    number_of_days: int | None = None,
    employees: dict[employee.EmployeeUid, employee.Employee] | None = None,
    shift_types: dict[shiftType.TypeUid, shiftType.ShiftType]
    | None = None,  # (day, shifttype_id) -> (employee_id ->, weight)
    shift_on_requests: dict[tuple[int, int], dict[int, int]] = defaultdict(dict),
    # (day, shifttype_id) -> (employee_id -> weight)
    shift_off_requests: dict[tuple[int, int], dict[int, int]] = defaultdict(dict),
    # (day, shifttype_id) -> (preffert_number_employees, weight_under, weight_over)
    cover_requirements: dict[tuple[int, int], tuple[int, int, int]] = defaultdict(
        tuple
    ),
) -> "instace.Instance":
    if number_of_days is None:
        number_of_days = instance.number_of_days
    if employees is None:
        employees = instance.employees
    if shift_types is None:
        print("this is wrong shift should not be None")
        shift_types = instance.shift_types
    if len(shift_on_requests) == 0:  # create shift_on_requests
        for day in range(number_of_days):
            for shifttype_uid in shift_types.keys():
                shift_on_requests[(int(day), int(shifttype_uid))] = instance.get_shift(
                    day=day, type_uid=shifttype_uid
                ).penalty_assigned_day_employee
    if len(shift_off_requests) == 0:  # create shift_off_requests
        for day in range(number_of_days):
            for shifttype_uid in shift_types.keys():
                shift_off_requests[(int(day), int(shifttype_uid))] = instance.get_shift(
                    day=day, type_uid=shifttype_uid
                ).penalty_not_assigned_day_employee
    if len(cover_requirements) == 0:  # create cover_requirements
        for day in range(number_of_days):
            for shifttype_uid in shift_types.keys():
                preffert_number_employees = instance.get_shift(
                    day=day, type_uid=shifttype_uid
                ).preffert_number_employees
                weight_below_preferred = instance.get_shift(
                    day=day, type_uid=shifttype_uid
                ).weight_below_preferred
                weight_above_preferred = instance.get_shift(
                    day=day, type_uid=shifttype_uid
                ).weight_above_preferred
                cover_requirements[(int(day), int(shifttype_uid))] = (
                    preffert_number_employees,
                    weight_below_preferred,
                    weight_above_preferred,
                )
    return instace.Instance.create(
        name=name,
        number_of_days=number_of_days,
        shift_typs=list(shift_types.values()),
        emplyees=list(employees.values()),
        shift_on_requests=shift_on_requests,
        shift_off_requests=shift_off_requests,
        cover_requirements=cover_requirements,
    )
