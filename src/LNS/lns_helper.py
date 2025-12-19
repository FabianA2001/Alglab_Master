from .. import solution
from ..module.solverConstraints import SolverConstraints


# TODO update function
def calculate_objective_value(sol: solution.Solution) -> float:
    """
    Berechnet den objective value einer Lösung basierend auf den Zuweisungen.
    """
    objective_value = 0.0

    # Penalty für Mitarbeiter-Zuweisungen
    for employee_uid in sol.instance.employees:
        for day in range(sol.instance.number_of_days):
            for type_uid in sol.instance.shifts[day]:
                is_assigned = sol.vars.get((day, type_uid, employee_uid), 0)

                # Penalty wenn NICHT zugewiesen (aber gewünscht)
                objective_value += sol.instance.get_shift(
                    day=day, type_uid=type_uid
                ).penalty_assigned_day_employee.get(employee_uid, 0) * (1 - is_assigned)

                # Penalty wenn zugewiesen (aber nicht gewünscht)
                objective_value += (
                    sol.instance.get_shift(
                        day=day, type_uid=type_uid
                    ).penalty_not_assigned_day_employee.get(employee_uid, 0)
                    * is_assigned
                )

    # Penalty für above/below preferred
    for day in range(sol.instance.number_of_days):
        for type_uid in sol.instance.shifts[day]:
            below = sol.below_prefferd_vars.get((day, type_uid), 0)
            above = sol.above_prefferd_vars.get((day, type_uid), 0)

            objective_value += (
                below * sol.instance.shifts[day][type_uid].weight_below_preferred
            )
            objective_value += (
                above * sol.instance.shifts[day][type_uid].weight_above_preferred
            )

    return objective_value


def merge_solutions(
    old_solutions: solution.Solution,
    new_solution: solution.Solution,
    start_day: int,
    end_day: int,
    disabled_for_window: list[SolverConstraints] = [],
) -> solution.Solution:
    """
    Integriert die neue Lösung aus dem Suchfenster in die alte Gesamtlösung.

    Args:
        new_solution: Die neue Lösung aus dem Suchfenster

    Returns:
        Eine neue Solution-Instanz mit den integrierten Änderungen
    """
    # Erstelle eine Kopie der alten Lösung
    import copy

    updated_solution = copy.deepcopy(old_solutions)

    updated_solution.disabled_constraints = new_solution.disabled_constraints

    # Iteriere über alle Tage im erweiterten Fenster
    for window_day in range(end_day - start_day + 1):
        original_day = start_day + window_day

        # Kopiere alle Shift-Zuweisungen für diesen Tag
        for shift_type_uid in updated_solution.instance.shift_types:
            for emp_uid in updated_solution.instance.employees:
                # Hole den Wert aus der neuen Lösung
                new_value = new_solution.vars[(window_day, shift_type_uid, emp_uid)]
                # Setze den Wert in der kopierten Lösung
                updated_solution.set_var(
                    original_day, shift_type_uid, emp_uid, new_value
                )
        # Kopiere Weekend-Variablen falls der Tag ein Wochenendtag ist
        if original_day in updated_solution.instance.weekend_days:
            for emp_uid in updated_solution.instance.employees:
                new_weekend_value = new_solution.weekend_vars.get(
                    (window_day, emp_uid), 0
                )
                updated_solution.set_weekend_var(
                    original_day, emp_uid, new_weekend_value
                )

        # Kopiere above/below preferred Variablen
        for shift_type_uid in updated_solution.instance.shift_types:
            new_above = new_solution.above_prefferd_vars.get(
                (window_day, shift_type_uid), 0
            )
            new_below = new_solution.below_prefferd_vars.get(
                (window_day, shift_type_uid), 0
            )
            updated_solution.set_above_prefferd_var(
                original_day, shift_type_uid, new_above
            )
            updated_solution.set_below_prefferd_var(
                original_day, shift_type_uid, new_below
            )

    # Berechne den neuen objective value der gesamten Lösung
    objective_value = calculate_objective_value(updated_solution)
    updated_solution.set_objective_value(objective_value)
    updated_solution.disabled_constraints = disabled_for_window

    return updated_solution
