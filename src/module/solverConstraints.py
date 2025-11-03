import enum


class SolverConstraints(enum.Enum):
    cover_requirements = enum.auto()
    days_off = enum.auto()
    limited_shifts_per_type_validation = enum.auto()
    max_Cons_Shifts = enum.auto()
    max_weekend_days = enum.auto()
    minimum_consecutive_days_off = enum.auto()
    minimum_consecutive_shifts = enum.auto()
    minMaxWorkTime = enum.auto()
    shift_assignment_single_day_validation = enum.auto()
    shift_rotation_constraint = enum.auto()
