from collections import defaultdict
from pathlib import Path

from ..inputTypes import employee, instace, shiftType


def parse_txt(txt_file_path: Path) -> instace.Instance:
    with open(txt_file_path, "r") as file:
        lines = [
            line.strip() for line in file if line.strip() and not line.startswith("#")
        ]

    horizon = 0
    shifts: list[shiftType.ShiftType] = []
    staff: dict[employee.EmployeeUid, employee.Employee] = {}
    # (day, shifttype_id) -> (employee_id ->, weight)
    shift_on_requests: dict[tuple[int, int], dict[int, int]] = defaultdict(dict)
    # (day, shifttype_id) -> (employee_id -> weight)
    shift_off_requests: dict[tuple[int, int], dict[int, int]] = defaultdict(dict)
    # (day, shifttype_id) -> (requirement, weight_under, weight_over)
    cover_requirements: dict[tuple[int, int], tuple[int, int, int]] = {}

    current_section = None

    for line in lines:
        if line.startswith("SECTION_"):
            current_section = line
            continue

        if current_section == "SECTION_HORIZON":
            horizon = int(line)

        elif current_section == "SECTION_SHIFTS":
            parts = line.split(",")
            shift_id = parts[0]
            length = int(parts[1])
            forbidden = parts[2].split("|") if parts[2] else []
            blocked_shifts_after = set()
            for fs in forbidden:
                blocked_shifts_after.add(hash(fs))
            shifts.append(
                shiftType.ShiftType(
                    uid=hash(shift_id),
                    length=length,
                    blocked_shifts_after=blocked_shifts_after,
                    name=shift_id,
                )
            )

        elif current_section == "SECTION_STAFF":
            parts = line.split(",")
            staff_id = parts[0]
            max_shifts = {}
            for shift_constraint in parts[1].split():
                for shift_constraint in parts[1].split("|"):
                    if "=" in shift_constraint:
                        shift, count = shift_constraint.split("=")
                        max_shifts[shift] = int(count)
                    else:
                        raise ValueError("Invalid shift constraint format")
            id = hash(staff_id)
            staff[id] = employee.Employee(
                uid=id,
                name=staff_id,
                max_numbers_of_shifts={
                    hash(shift): count for shift, count in max_shifts.items()
                },
                max_minutes_assigned=int(parts[2]),
                min_minutes_assigned=int(parts[3]),
                max_number_consecutive_shifts=int(parts[4]),
                min_number_consecutive_shifts=int(parts[5]),
                min_number_consecutive_days_off=int(parts[6]),
                max_number_weekends=int(parts[7]),
            )

        elif current_section == "SECTION_DAYS_OFF":
            parts = line.split(",")
            employee_id = parts[0]
            day_indexes = set(int(d) for d in parts[1:])
            staff[hash(employee_id)].blocked_shifts = day_indexes

        elif current_section == "SECTION_SHIFT_ON_REQUESTS":
            parts = line.split(",")
            shift_on_requests[(int(parts[1]), hash(parts[2]))][hash(parts[0])] = int(
                parts[3]
            )

        elif current_section == "SECTION_SHIFT_OFF_REQUESTS":
            parts = line.split(",")
            shift_off_requests[(int(parts[1]), hash(parts[2]))][hash(parts[0])] = int(
                parts[3]
            )

        elif current_section == "SECTION_COVER":
            parts = line.split(",")
            cover_requirements[(int(parts[0]), hash(parts[1]))] = (
                int(parts[2]),
                int(parts[3]),
                int(parts[4]),
            )

    return instace.Instance.create(
        name=txt_file_path.stem,
        number_of_days=horizon,
        shift_typs=shifts,
        emplyees=list(staff.values()),
        shift_on_requests=shift_on_requests,
        shift_off_requests=shift_off_requests,
        cover_requirements=cover_requirements,
    )
