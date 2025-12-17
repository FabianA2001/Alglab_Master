from datetime import datetime

from ortools.sat.python import cp_model

from .. import shift_vars
from ..inputTypes import instace
from ..solution import Solution


class CollectAllSolutions(cp_model.CpSolverSolutionCallback):
    """Callback that collects every solution found by the solver.

    The callback stores full `Solution` objects in `self.collected` so the caller
    can post-process/rank them (for example by counting changes vs. a base
    solution).
    """

    def __init__(
        self,
        instance: instace.Instance,
        vars: shift_vars.Shift_vars,
        disabled_constraints: list = [],
        start_time=None,
    ):
        super().__init__()
        self.instance = instance
        self.vars = vars
        self.disabled_constraints = disabled_constraints
        self.start_time = start_time
        self.collected: list[Solution] = []

    def on_solution_callback(self):
        sol = Solution(self.instance)

        # store assignment vars
        for day in range(self.instance.number_of_days):
            for type_uid in self.instance.shifts[day]:
                for employee_uid in self.instance.employees:
                    val = self.Value(self.vars.get_var(day, type_uid, employee_uid))
                    sol.set_var(day, type_uid, employee_uid, val)

        # weekends
        for weekend in range(round(self.instance.number_of_days / 7)):
            for employee_uid in self.instance.employees:
                weekend_value = self.Value(
                    self.vars.get_weekend_var(weekend, employee_uid)
                )
                sol.set_weekend_var(weekend, employee_uid, weekend_value)

        # above/below preferred
        for day in range(self.instance.number_of_days):
            for type_uid in self.instance.shifts[day]:
                above_value = self.Value(
                    self.vars.get_above_prefferd_var(day, type_uid)
                )
                below_value = self.Value(
                    self.vars.get_below_prefferd_var(day, type_uid)
                )
                sol.set_above_prefferd_var(day, type_uid, above_value)
                sol.set_below_prefferd_var(day, type_uid, below_value)

        sol.objective_value = self.ObjectiveValue()
        sol.instance = self.instance
        sol.disabled_constraints = self.disabled_constraints
        sol.solve_status = cp_model.FEASIBLE
        if self.start_time is not None:
            sol.solve_time = (datetime.now() - self.start_time).total_seconds()
        else:
            sol.solve_time = 0
        sol.timestamp = datetime.now()

        self.collected.append(sol)
