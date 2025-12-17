import copy

from ..inputTypes.instace import Instance
from ..solution import Solution
from .slice_instance import Slice_instance

PADDING = 2


def __solve_change(
    old_solution: Solution,
    new_instanc: Instance,
    start_day: int,
    end_day: int,
    max_solve_time: int,
) -> Solution:
    updated_solution = copy.deepcopy(old_solution)
    solver = Slice_instance(
        sol=updated_solution, inst=new_instanc, start=start_day, end=end_day
    ).get_solver()
    # TODO min changs callback
    return solver.solve_window(max_time_in_seconds=max_solve_time)


def solve_changes(
    old_solution: Solution,
    new_instanc: Instance,
    days_with_change: list[int],
    max_solve_time: int = 60,
) -> Solution:
    assert old_solution.instance.number_of_days == new_instanc.number_of_days, (
        "Die Anzahl der Tage in der alten und neuen Instanz muss übereinstimmen."
    )
    assert len(days_with_change) > 0, "Es wurden keine Tage mit Änderungen angegeben."
    small_max_solve_time = max_solve_time // len(days_with_change)
    for day in days_with_change:
        start_day = max(0, day - PADDING)
        end_day = min(new_instanc.number_of_days - 1, day + PADDING)

        old_solution = __solve_change(
            old_solution, new_instanc, start_day, end_day, small_max_solve_time
        )
    return old_solution
