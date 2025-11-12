import enum


class Session_state_Names(enum.Enum):
    instance = enum.auto()
    solutions = enum.auto()
    allow_resolve = enum.auto()
    disabled_constraints = enum.auto()
    solver_running = enum.auto()
    solver_executor = enum.auto()
    solver_future = enum.auto()
    solver_start_time = enum.auto()
