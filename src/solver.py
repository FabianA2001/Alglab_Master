from ortools.sat.python import cp_model
from . import shift_vars
from .inputTypes import instace
from .solution import Solution


class Solver:
    def __init__(self, instance: instace.Instance, vars: shift_vars.Shift_vars):
        self.instance = instance
        self.vars = vars

    def solve(
        self,
        log_search_progress: bool = True,
        max_time_in_seconds: float = 60.0,
        **solver_params,
    ) -> Solution:
        solver = cp_model.CpSolver()
        solver.parameters.log_search_progress = log_search_progress
        solver.parameters.max_time_in_seconds = max_time_in_seconds

        for key, value in solver_params.items():
            setattr(solver.parameters, key, value)

        self.vars.model.Minimize(self.objevtive_value())
        status = solver.Solve(self.vars.model)
        return self.handle_results(status, solver)

    def objevtive_value(self):
        objective_value = 0
        for employee_uid in self.instance.employees:
            for day in range(self.instance.number_of_days):
                for type_uid in self.instance.shifts[day]:
                    objective_value += self.instance.shifts[day][
                        type_uid
                    ].penalty_not_assigned_day_employee[employee_uid] * (
                        1 - self.vars.vars[(day, type_uid, employee_uid)]
                    )
                    objective_value += (
                        self.instance.shifts[day][
                            type_uid
                        ].penalty_assigned_day_employee[employee_uid]
                        * self.vars.vars[(day, type_uid, employee_uid)]
                    )
        for day in range(self.instance.number_of_days):
            for type_uid in self.instance.shifts[day]:
                objective_value += (
                    self.vars.below_prefferd_vars[day][type_uid]
                    * self.instance.shifts[day][type_uid].weight_below_preferred
                )
                objective_value += (
                    self.vars.above_prefferd_vars[day][type_uid]
                    * self.instance.shifts[day][type_uid].weight_above_preferred
                )
        return objective_value

    def handle_results(self, status, solver: cp_model.CpSolver) -> Solution:
        """Handles the different results returned by the solver and returns a solution."""
        solution = Solution()  # Create a new Solution instance
        if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
            self.store_solution(
                solver, solution
            )  # Pass the solution instance to store values
            if status == cp_model.OPTIMAL:
                print("Optimal solution found.")
            else:
                print("Feasible solution found but not optimal.")
            solution.objective_value = solver.ObjectiveValue()
            solution.instance = self.instance
            return solution  # Return the populated solution
        elif status == cp_model.INFEASIBLE:
            self.process_infeasible_solution()
        elif status == cp_model.UNKNOWN:
            self.process_unknown_status()
        elif status == cp_model.MODEL_INVALID:
            self.process_invalid_model()

        return solution  # Return an empty solution for cases where no valid solution was found

    def store_solution(self, solver: cp_model.CpSolver, solution: Solution) -> None:
        """Stores the solution in the given Solution instance."""
        for day in range(self.instance.number_of_days):
            for type_uid in self.instance.shifts[day]:
                for employee_uid in self.instance.employees:
                    var_value = solver.Value(
                        self.vars.get_var(day, type_uid, employee_uid)
                    )
                    solution.set_var(day, type_uid, employee_uid, var_value)

        for weekend in self.instance.weekend_days:
            for employee_uid in self.instance.employees:
                weekend_value = solver.Value(
                    self.vars.get_weekend_var(weekend, employee_uid)
                )
                solution.set_weekend_var(weekend, employee_uid, weekend_value)

        # Store above and below preferred vars
        for day in range(self.instance.number_of_days):
            for type_uid in self.instance.shifts[day]:
                above_value = solver.Value(
                    self.vars.get_above_prefferd_var(day, type_uid)
                )
                below_value = solver.Value(
                    self.vars.get_below_prefferd_var(day, type_uid)
                )
                solution.set_above_prefferd_var(day, type_uid, above_value)
                solution.set_below_prefferd_var(day, type_uid, below_value)

    def process_infeasible_solution(self) -> None:
        """Handles the case when no feasible solution exists."""
        print("No feasible solution exists for the provided constraints.")

    def process_unknown_status(self) -> None:
        """Handles the case when the solver stops without finding a solution."""
        print(
            "Solver stopped without finding a solution. Possible reasons may include time limits or resource limits."
        )

    def process_invalid_model(self) -> None:
        """Handles the case when the model is invalid."""
        print("The model provided is invalid and cannot be solved.")
