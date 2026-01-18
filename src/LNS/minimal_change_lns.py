import copy

from ortools.sat.python import cp_model

from ..solution import Solution
from .lns_helper import merge_solutions
from .slice_instance import Slice_instance

# Original 2
# getestet mit 10
# getestet mit 40

PADDING = 3


def __solve_change(
    old_solution: Solution,
    start_day: int,
    end_day: int,
    max_solve_time: int,
    log_search_progress: bool = True,
) -> Solution:
    updated_solution = copy.deepcopy(old_solution)
    slice_instance = Slice_instance(sol=updated_solution, start=start_day, end=end_day)
    solver = slice_instance.get_solver()
    # TODO min changs callback
    return solver.solve_window_min_changes(
        solution=slice_instance.slice_solution,
        log_search_progress=log_search_progress,
        max_time_in_seconds=max_solve_time,
    )


def solve_changes(
    old_solution: Solution,
    days_with_change: list[int],
    max_solve_time: int = 60,
    log_search_progress: bool = True,
) -> Solution:
    new_instanc = old_solution.instance
    assert old_solution.instance.number_of_days == new_instanc.number_of_days, (
        "Die Anzahl der Tage in der alten und neuen Instanz muss übereinstimmen."
    )
    assert len(days_with_change) > 0, "Es wurden keine Tage mit Änderungen angegeben."
    # small_max_solve_time = max_solve_time // len(days_with_change)
    small_max_solve_time = max_solve_time
    days_with_change_copy = list(days_with_change)
    while days_with_change_copy:
        day = days_with_change_copy[0]
        print(f"Löse Änderungen für Tag {day}...")
        start_day = max(0, day - PADDING)
        end_day = min(new_instanc.number_of_days - 1, day + PADDING)
        dmin = new_instanc.number_of_days
        for d in days_with_change_copy:
            if d >= day - PADDING and d < day and d < dmin:
                start_day = max(0, d - PADDING)
                dmin = d
            if d <= day + PADDING and d > day:
                end_day = min(new_instanc.number_of_days - 1, d + PADDING)
        counter = 0
        for d in days_with_change_copy:
            if d >= start_day and d <= end_day:
                counter += 1
        days_with_change_copy = [
            d for d in days_with_change_copy if d < start_day or d > end_day
        ]
        new_solution = __solve_change(
            old_solution,
            start_day,
            end_day,
            small_max_solve_time,
            log_search_progress=log_search_progress,
        )
        if not (
            new_solution.solve_status == cp_model.OPTIMAL
            or new_solution.solve_status == cp_model.FEASIBLE
        ):
            # TODO behandeln
            print(f"Kein Lösungsstatus für das Fenster {start_day}-{end_day} gefunden.")
            infeasible = True
            i = 1
            reached_start = False
            reached_end = False
            # TODO (Fabian) Müsste number_of_days nicht durch 2 geteilt werden weil Padding in beide Richtungen erweitert wird?
            # TODO (Fabian) Small solve time muss angepasst werden weil es jetzt ja pro trag theoretisch mehrmals versucht wird
            while infeasible and ((not reached_start) or (not reached_end)):
                print(
                    f"Erneuter Versuch mit mehr Padding: {PADDING + ((3 + counter) * i)}"
                )
                start_day = max(0, day - (PADDING + ((3 + counter) * i)))

                end_day = min(
                    new_instanc.number_of_days - 1,
                    day + (PADDING + ((3 + counter) * i)),
                )
                dmin = new_instanc.number_of_days
                for d in days_with_change_copy:
                    if d >= start_day and d < day and d < dmin:
                        start_day = max(0, day - (PADDING + ((3 + counter) * i)))
                        dmin = d
                    if d <= end_day and d > day:
                        end_day = min(
                            new_instanc.number_of_days - 1,
                            day + (PADDING + ((3 + counter) * i)),
                        )

                days_with_change_copy = [
                    d for d in days_with_change_copy if d < start_day or d > end_day
                ]
                reached_start = start_day == 0
                reached_end = end_day == new_instanc.number_of_days - 1
                new_solution = __solve_change(
                    old_solution,
                    start_day,
                    end_day,
                    small_max_solve_time,
                    log_search_progress=log_search_progress,
                )
                i += 1
                if (
                    new_solution.solve_status == cp_model.OPTIMAL
                    or new_solution.solve_status == cp_model.FEASIBLE
                ):
                    print(f"Lösung gefunden mit mehr Padding: {PADDING + (3 * i)}")
                    infeasible = False
        print("Lösung gefunden ohne extra padding")
        # TODO (Fabian) testen ob die neue soltions feasible ist
        old_solution = merge_solutions(
            old_solutions=old_solution,
            new_solution=new_solution,
            start_day=start_day,
            end_day=end_day,
        )
        if not old_solution.checkt_constraints[0]:
            assert False, (
                f"Die zusammengeführte Lösung für das Fenster {start_day}-{end_day} verletzt die Nebenbedingungen."
            )

    return old_solution
