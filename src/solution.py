from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Dict, Tuple

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator

from .inputTypes import employee, instace, shift
from .module.solverConstraints import SolverConstraints

if TYPE_CHECKING:
    pass  # Forward reference für Solution wird später definiert

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "solutions"


class Solution(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    def __init__(self, instance: instace.Instance, **data):
        super().__init__(instance=instance, **data)

    """Class to handle variable storage and management for shift scheduling."""

    vars: Dict[Tuple[int, shift.ShiftUid, employee.EmployeeUid], int] = Field(
        default_factory=dict,
        description="Mapping of boolean variables that indicate whether a specific employee is assigned to a given shift on a specified day. The key is a tuple of (day, shift type, employee ID).",
    )

    work_vars: Dict[Tuple[int, employee.EmployeeUid], int] = Field(
        default_factory=dict,
        description="Mapping of boolean variables that indicate whether a specific employee is assigned to a given shift on a specified day. The key is a tuple of (day, shift type, employee ID).",
    )

    weekend_vars: Dict[Tuple[int, employee.EmployeeUid], int] = Field(
        default_factory=dict,
        description="Mapping of boolean variables that indicate whether a specific employee is working on a weekend day. The key is a tuple of (weekend day, employee ID).",
    )

    above_prefferd_vars: Dict[Tuple[int, shift.ShiftUid], int] = Field(
        default_factory=dict,
        description="Mapping of integer variables representing the excess number of employees assigned to a shift above its preferred capacity. The key is a tuple of (day, shift type).",
    )

    below_prefferd_vars: Dict[Tuple[int, shift.ShiftUid], int] = Field(
        default_factory=dict,
        description="Mapping of integer variables representing the shortfall of employees assigned to a shift below its preferred capacity. The key is a tuple of (day, shift type).",
    )
    instance: instace.Instance = Field(
        description="An instance that contains all given variables",
    )
    objective_value: float = Field(
        default=0.0,
        description="The result of an objective function",
    )
    disabled_constraints: list[SolverConstraints] = Field(
        default_factory=list,
        description="List of disabled solver constraints",
    )
    solve_time: float = Field(
        default_factory=float, description="Time taken to solve the instance in seconds"
    )
    solve_status: int = Field(
        default_factory=int, description="Status code returned by the solver"
    )
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Timestamp when the solution was created",
    )

    @computed_field
    @property
    def checkt_constraints(self) -> tuple[bool, dict[str, tuple[bool, list[str]]]]:
        return _check_all_constraints(self)

    @field_validator("vars", mode="before")
    @classmethod
    def validate_vars(cls, v: Any) -> Dict[Tuple[int, int, int], int]:
        """Convert string keys back to tuple keys for vars field."""
        if isinstance(v, dict):
            return {
                tuple(map(int, k.split(","))) if isinstance(k, str) else k: val
                for k, val in v.items()
            }  # type: ignore
        return v
    
    @field_validator("work_vars", mode="before")
    @classmethod
    def validate_work_vars(cls, v: Any) -> Dict[Tuple[int, int], int]:
        """Convert string keys back to tuple keys for work_vars field."""
        if isinstance(v, dict):
            return {
                (int(k.split(",")[0]), employee.EmployeeUid(int(k.split(",")[1]))) if isinstance(k, str) else k: val
                for k, val in v.items()
            }  # type: ignore
        return v

    @field_validator("weekend_vars", mode="before")
    @classmethod
    def validate_weekend_vars(cls, v: Any) -> Dict[Tuple[int, int], int]:
        """Convert string keys back to tuple keys for weekend_vars field."""
        if isinstance(v, dict):
            return {
                tuple(map(int, k.split(","))) if isinstance(k, str) else k: val
                for k, val in v.items()
            }  # type: ignore
        return v

    @field_validator("above_prefferd_vars", mode="before")
    @classmethod
    def validate_above_prefferd_vars(cls, v: Any) -> Dict[Tuple[int, int], int]:
        """Convert string keys back to tuple keys for above_prefferd_vars field."""
        if isinstance(v, dict):
            return {
                tuple(map(int, k.split(","))) if isinstance(k, str) else k: val
                for k, val in v.items()
            }  # type: ignore
        return v

    @field_validator("below_prefferd_vars", mode="before")
    @classmethod
    def validate_below_prefferd_vars(cls, v: Any) -> Dict[Tuple[int, int], int]:
        """Convert string keys back to tuple keys for below_prefferd_vars field."""
        if isinstance(v, dict):
            return {
                tuple(map(int, k.split(","))) if isinstance(k, str) else k: val
                for k, val in v.items()
            }  # type: ignore
        return v

    def set_var(self, day: int, type_uid: int, employee_uid: int, value: int):
        """Sets the boolean variable value."""
        self.vars[(day, type_uid, employee_uid)] = value
    def set_work_vars(self, day: int, employee_uid: int, value: int):
        self.work_vars[(day, employee_uid)] = value
    def set_weekend_var(self, weekend: int, employee_uid: int, value: int):
        """Sets the weekend variable value."""
        self.weekend_vars[(weekend, employee_uid)] = value

    def set_above_prefferd_var(self, day: int, type_uid: int, value: int):
        """Sets the above preferred variable value."""
        self.above_prefferd_vars[(day, type_uid)] = value

    def set_below_prefferd_var(self, day: int, type_uid: int, value: int):
        """Sets the below preferred variable value."""
        self.below_prefferd_vars[(day, type_uid)] = value

    def set_instance(self, instance: instace.Instance):
        self.instance = instance

    def set_objective_value(self, objective_value: float):
        self.objective_value = objective_value

    def is_employee_assigned(
        self, day: int, shift_type_uid: int, employee_uid: int
    ) -> bool:
        """Überprüft, ob ein Mitarbeiter einem bestimmten Schichttyp an einem bestimmten Tag zugewiesen ist."""

        return self.vars[(day, shift_type_uid, employee_uid)] == 1

    # def print_assign(self):
    #     for day, type_uid, employee_uid in self.vars.keys():
    #         print(
    #             f"assign_{day}_{type_uid}_to_{employee_uid}: ",
    #             self.vars[(day, type_uid, employee_uid)],
    #         )
    def print_assign(self):
        """Gibt alle eingeteilten Employee-UIDs pro Tag aus (value == 1)."""
        print("=== Mitarbeiter-Zuordnung pro Tag ===")

        # Alle vorhandenen Tage aus den Variablen extrahieren
        days = sorted({day for (day, _, _) in self.vars.keys()})

        for day in days:
            # Alle Mitarbeiter, die an diesem Tag arbeiten (value == 1)
            assigned = [
                emp_uid
                for (d, _, emp_uid), value in self.vars.items()
                if d == day and value == 1
            ]

            # Ausgabe
            print(f"\nTag {day}:")
            if assigned:
                for emp_uid in assigned:
                    print(f"  - {self.instance.employees[emp_uid].name}")
            else:
                print("  (Niemand eingeteilt)")

    # def print_assign(self):
    #     """Gibt alle eingeteilten Mitarbeiter (A, B, C, ...) pro Tag aus."""
    #     print("=== Mitarbeiter-Zuordnung pro Tag ===")

    #     # Alle vorhandenen Mitarbeiter-UIDs extrahieren und sortieren
    #     employee_uids = sorted(
    #         {emp_uid for (_, _, emp_uid) in self.vars.keys()})

    #     # Jedem Employee-UID einen Buchstaben zuweisen: A, B, C, ...
    #     name_map = {
    #         uid: string.ascii_uppercase[i % 26] +
    #         (str(i // 26 + 1) if i >= 26 else "")
    #         for i, uid in enumerate(employee_uids)
    #     }
    #     # (Falls du mehr als 26 Mitarbeitende hast, geht’s weiter mit A1, B1, C1, …)

    #     # Alle vorhandenen Tage extrahieren
    #     days = sorted({day for (day, _, _) in self.vars.keys()})

    #     # Ausgabe
    #     for day in days:
    #         assigned = [
    #             name_map[emp_uid]
    #             for (d, _, emp_uid), value in self.vars.items()
    #             if d == day and value == 1
    #         ]
    #         print(f"\nTag {day}:")
    #         if assigned:
    #             for name in assigned:
    #                 print(f"  - {name}")
    #         else:
    #             print("  (Niemand eingeteilt)")

    def print_assign_values(self):
        for day, type_uid, employee_uid in self.vars.keys():
            print(
                f"assign_{day}_{self.instance.shift_types[type_uid].name}_to_{self.instance.employees[employee_uid].name}: ",
                self.vars[(day, type_uid, employee_uid)],
            )

    def print_weekend_work_values(self):
        for weekend, employee_uid in self.weekend_vars.keys():
            print(
                f"weekend_work_{weekend}_for_{self.instance.employees[employee_uid].name}: ",
                self.weekend_vars[(weekend, employee_uid)],
            )

    def print_below_prefferd_values(self):
        for day, type_uid in self.below_prefferd_vars.keys():
            print(
                f"below_prefferd_{day}_{self.instance.shift_types[type_uid].name}: ",
                self.below_prefferd_vars[(day, type_uid)],
            )

    def print_assign_above_prefferd_values(self):
        for day, type_uid in self.above_prefferd_vars.keys():
            print(
                f"above_prefferd_{day}_{self.instance.shift_types[type_uid].name}: ",
                self.above_prefferd_vars[(day, type_uid)],
            )

    def print_weekend_work(self):
        for weekend, employee_uid in self.weekend_vars.keys():
            print(
                f"weekend_work_{weekend}_for_{employee_uid}: ",
                self.weekend_vars[(weekend, employee_uid)],
            )

    def print_below_prefferd(self):
        for day, type_uid in self.below_prefferd_vars.keys():
            print(
                f"below_prefferd_{day}_{type_uid}: ",
                self.below_prefferd_vars[(day, type_uid)],
            )

    def print_assign_above_prefferd(self):
        for day, type_uid in self.above_prefferd_vars.keys():
            print(
                f"above_prefferd_{day}_{type_uid}: ",
                self.above_prefferd_vars[(day, type_uid)],
            )

    def print_all_variables(self):
        self.print_assign()
        print("\n" * 2)
        self.print_weekend_work()
        print("\n" * 2)
        self.print_below_prefferd()
        print("\n" * 2)
        self.print_assign_above_prefferd()

    def print_all_variables_values(self):
        self.print_assign_values()
        print("\n" * 2)
        self.print_weekend_work_values()
        print("\n" * 2)
        self.print_below_prefferd_values()
        print("\n" * 2)
        self.print_assign_above_prefferd_values()

    def to_json_file(self, name: str):
        """Speichert die Solution als JSON-Datei mit Pydantic's model_dump_json().

        Args:
            filepath: Pfad zur JSON-Datei
        """
        path = DATA_DIR / f"{name}.json"
        path.parent.mkdir(parents=True, exist_ok=True)

        # Nutze Pydantic's eingebaute JSON-Serialisierung
        json_str = self.model_dump_json(indent=2)

        with open(path, "w", encoding="utf-8") as f:
            f.write(json_str)

        print(f"Solution gespeichert in: {path}")

    @classmethod
    def from_json_file(cls, name: str) -> "Solution":
        """Lädt eine Solution aus einer JSON-Datei mit Pydantic's model_validate_json().

        Args:
            filepath: Pfad zur JSON-Datei

        Returns:
            Solution: Die geladene Solution
        """
        path = DATA_DIR / f"{name}.json"

        if not path.exists():
            raise FileNotFoundError(f"Datei nicht gefunden: {path}")

        with open(path, "r", encoding="utf-8") as f:
            json_str = f.read()

        # Nutze Pydantic's eingebaute JSON-Deserialisierung
        solution = cls.model_validate_json(json_str)

        print(f"Solution geladen aus: {path}")

        return solution
    

    @classmethod
    def delete_json_solution(cls, name: str) -> None:
        """Delete a JSON file corresponding to the Solution.

        Args:
            name: Name of the Solution, without the .json extension.
        """
        path = DATA_DIR / f"{name}.json"

        if path.exists():
            path.unlink()  # Delete the file
            print(f"Datei gelöscht: {path}")
        else:
            print(f"Datei nicht gefunden: {path}")

    def minimal_shift_fulfillment(self) -> float:
        """Return the minimum fulfillment ratio across all shifts."""
        min_fulfillment = float('inf')

        for day, day_shift_dict in self.instance.shifts.items():
            for type_uid, shift in day_shift_dict.items():
                filled_count = sum(1 for emp in self.instance.employees if self.vars.get((day, type_uid, emp), 0) == 1)
                total_required = shift.preffert_number_employees
                
                # Calculate the fulfillment ratio
                if total_required > 0:
                    fulfillment_ratio = filled_count / total_required
                    min_fulfillment = min(min_fulfillment, fulfillment_ratio)

        return min_fulfillment if min_fulfillment != float('inf') else 1

    def maximum_shift_fulfillment(self) -> float:
        """Return the maximum fulfillment ratio across all shifts."""
        max_fulfillment = float('-inf')

        for day, day_shift_dict in self.instance.shifts.items():
            for type_uid, shift in day_shift_dict.items():
                filled_count = sum(1 for emp in self.instance.employees if self.vars.get((day, type_uid, emp), 0) == 1)
                total_required = shift.preffert_number_employees
                
                # Calculate the fulfillment ratio
                if total_required > 0:
                    fulfillment_ratio = filled_count / total_required
                    max_fulfillment = max(max_fulfillment, fulfillment_ratio)

        return max_fulfillment if max_fulfillment != float('-inf') else 1

    def average_shift_fulfillment(self) -> float:
        """Return the average fulfillment ratio across all shifts."""
        total_fulfillment = 0.0
        shift_count = 0

        for day, day_shift_dict in self.instance.shifts.items():
            for type_uid, shift in day_shift_dict.items():
                filled_count = sum(1 for emp in self.instance.employees if self.vars.get((day, type_uid, emp), 0) == 1)
                total_required = shift.preffert_number_employees

                # Calculate the fulfillment ratio
                if total_required > 0:
                    fulfillment_ratio = filled_count / total_required
                    total_fulfillment += fulfillment_ratio
                    shift_count += 1

        return total_fulfillment / shift_count if shift_count > 0 else 1

    def _calculate_fulfillment_ratio(self, wishes_type: str):
        """Helper method to calculate fulfillment ratios for positive or negative wishes."""
        min_percentage = float('inf')  # For minimal
        max_percentage = float('-inf')  # For maximum
        total_percentage = 0.0
        count = 0

        for emp in self.instance.employees:
            total_wishes = 0
            fulfilled_wishes = 0

            for day, day_shift_dict in self.instance.shifts.items():
                for type_uid, shift in day_shift_dict.items():
                    if wishes_type == 'positive':
                        weight = shift.penalty_assigned_day_employee.get(emp, 0)
                    else:  # negative wishes
                        weight = shift.penalty_not_assigned_day_employee.get(emp, 0)

                    if weight > 0:
                        total_wishes += 1
                        if self.vars.get((day, type_uid, emp), 0) == (1 if wishes_type == 'positive' else 0):
                            fulfilled_wishes += 1

            if total_wishes > 0:
                percentage = fulfilled_wishes / total_wishes
                min_percentage = min(min_percentage, percentage)
                max_percentage = max(max_percentage, percentage)
                total_percentage += percentage
                count += 1

        # Return appropriate values based on the type of fulfillment requested
        if wishes_type == 'positive':
            return min_percentage if min_percentage != float('inf') else 1, max_percentage if max_percentage != float('-inf') else 1, total_percentage / count if count > 0 else 1
        else:
            return min_percentage if min_percentage != float('inf') else 1, max_percentage if max_percentage != float('-inf') else 1, total_percentage / count if count > 0 else 1

    def minimal_employee_positive_wishes_met(self) -> float:
        return self._calculate_fulfillment_ratio('positive')[0]  # Return min

    def maximum_employee_positive_wishes_met(self) -> float:
        return self._calculate_fulfillment_ratio('positive')[1]  # Return max

    def average_employee_positive_wishes_met(self) -> float:
        return self._calculate_fulfillment_ratio('positive')[2]  # Return average

    def minimal_employee_negative_wishes_met(self) -> float:
        return self._calculate_fulfillment_ratio('negative')[0]  # Return min

    def maximum_employee_negative_wishes_met(self) -> float:
        return self._calculate_fulfillment_ratio('negative')[1]  # Return max

    def average_employee_negative_wishes_met(self) -> float:
        return self._calculate_fulfillment_ratio('negative')[2]  # Return average


    def total_fulfilled_wishes(self) -> int:
        """Count total fulfilled positive and negative wishes."""
        total_fulfilled = 0

        # Counting positive wishes
        for emp in self.instance.employees:
            for day, day_shift_dict in self.instance.shifts.items():
                for type_uid, shift in day_shift_dict.items():
                    if shift.penalty_assigned_day_employee.get(emp, 0) > 0:
                        if self.vars.get((day, type_uid, emp), 0) == 1:
                            total_fulfilled += 1

        # Counting negative wishes (assumed similar logic)
        for emp in self.instance.employees:
            for day, day_shift_dict in self.instance.shifts.items():
                for type_uid, shift in day_shift_dict.items():
                    if shift.penalty_not_assigned_day_employee.get(emp, 0) > 0:
                        if self.vars.get((day, type_uid, emp), 0) == 0:
                            total_fulfilled += 1

        return total_fulfilled


    def median_employee_positive_wishes_met(self) -> float:
        """Return the median percentage of fulfilled positive wishes for all employees."""
        percentages = []

        for emp in self.instance.employees:
            total_positive_wishes = 0
            fulfilled_positive_wishes = 0

            for day, day_shift_dict in self.instance.shifts.items():
                for type_uid, shift in day_shift_dict.items():
                    weight_pos = shift.penalty_assigned_day_employee.get(emp, 0)
                    if weight_pos > 0:
                        total_positive_wishes += 1
                        if self.vars.get((day, type_uid, emp), 0) == 1:
                            fulfilled_positive_wishes += 1

            if total_positive_wishes > 0:
                percentages.append(fulfilled_positive_wishes / total_positive_wishes)

        if not percentages:  # No employee data
            return 1

        percentages.sort()
        n = len(percentages)
        mid = n // 2

        if n % 2 == 1:  # Odd number of elements
            return percentages[mid]
        else:  # Even number of elements
            return (percentages[mid - 1] + percentages[mid]) / 2

    def median_employee_negative_wishes_met(self) -> float:
        """Return the median percentage of fulfilled negative wishes for all employees."""
        percentages = []

        for emp in self.instance.employees:
            total_negative_wishes = 0
            fulfilled_negative_wishes = 0

            for day, day_shift_dict in self.instance.shifts.items():
                for type_uid, shift in day_shift_dict.items():
                    weight_neg = shift.penalty_not_assigned_day_employee.get(emp, 0)
                    if weight_neg > 0:
                        total_negative_wishes += 1
                        if self.vars.get((day, type_uid, emp), 0) == 0:
                            fulfilled_negative_wishes += 1

            if total_negative_wishes > 0:
                percentages.append(fulfilled_negative_wishes / total_negative_wishes)

        if not percentages:  # No employee data
            return 1

        percentages.sort()
        n = len(percentages)
        mid = n // 2

        if n % 2 == 1:  # Odd number of elements
            return percentages[mid]
        else:  # Even number of elements
            return (percentages[mid - 1] + percentages[mid]) / 2

    #TODO instead of updating below_prefferd_vars and above_prefferd_vars calculating using the self and the extra solution
    def copy_solution(self, solution: "Solution"):
        self.vars.update(solution.vars)
        self.weekend_vars.update(solution.weekend_vars)
        self.above_prefferd_vars.update(solution.above_prefferd_vars)
        self.work_vars.update(solution.work_vars)
        self.below_prefferd_vars.update(solution.below_prefferd_vars)
    
    def store_solution_vars(self, solution: "Solution", day: int | None = None, employee_uid: employee.EmployeeUid | None = None, shift_type_uid: shift.ShiftUid | None = None):
        if day is None:
            day_start = 0
            day_end = self.instance.number_of_days
        else:
            day_start = day
            day_end = day + 1

        if employee_uid is None:
            employees = self.instance.employees
        elif employee_uid in self.instance.employees.keys():
            employees = {employee_uid: self.instance.employees[employee_uid]}
        else:
            print(f"somthing bad happend: {employee_uid} is not in the instance")
            return

        if shift_type_uid is None:
            shifts_types = self.instance.shift_types
        elif shift_type_uid in self.instance.shift_types.keys():
            shifts_types = {shift_type_uid: self.instance.shift_types[shift_type_uid]}
        else:
            print(f"somthing bad happend: shift type {shift_type_uid} is not in the instance")
            return
        for day_ in range(day_start, day_end):
            for employee_uid, employee_ in employees.items():
                for shift_type_uid, shift_type in shifts_types.items():
                    if (day_, shift_type_uid, employee_uid) in solution.vars.keys():
                        self.set_var(day_, shift_type_uid, employee_uid, solution.vars[(day_, shift_type_uid, employee_uid)] == 1)
                    # else:
                    #     print(f"key var {(day_, shift_type_uid, employee_uid)} is not a key in the to be copied solution")


    def store_solution_work_vars(self, solution: "Solution", day: int | None = None, employee_uid: employee.EmployeeUid | None = None):
        if day is None:
            day_start = 0
            day_end = self.instance.number_of_days
        else:
            day_start = day
            day_end = day + 1

        if employee_uid is None:
            employees = self.instance.employees
        elif employee_uid in self.instance.employees.keys():
            employees = {employee_uid: self.instance.employees[employee_uid]}
        else:
            print(f"somthing bad happend: {employee_uid} is not in the instance")
            return
        for employee_uid, employee_ in employees.items():
            for day_ in range(day_start, day_end):
                if (day_, employee_uid) in solution.work_vars.keys():
                    self.set_work_vars(day_, employee_uid, solution.work_vars[(day_, employee_uid)] == 1)
                # else:
                #     print(f"key work var {(day_, employee_uid)} is not a key in the to be copied solution")
    


# Standalone constraint checking functions
# (moved here to avoid circular imports)
def _get_all_constraint_checks() -> list[
    Tuple[str, Callable[["Solution"], Tuple[bool, list[str]]]]
]:
    """Gibt eine Liste aller Constraint-Check-Funktionen zurück."""
    from .validation.basic_constraints import (
        check_cover_requirements_constraint,
        check_days_off_constraint,
        check_shift_rotation_constraint,
        check_single_day_constraint,
    )
    from .validation.shift_constraints import (
        check_lim_shifts_type_constraint,
        check_max_cons_shifts_constraint,
        check_min_cons_shifts_constraint,
        check_min_max_worktime_constraint,
    )
    from .validation.weekend_constraints import (
        check_max_weekend_days_constraint,
        check_min_cons_days_constraint,
    )

    return [
        ("Cover Requirements", check_cover_requirements_constraint),
        ("Days Off", check_days_off_constraint),
        ("Limited Shifts per Type", check_lim_shifts_type_constraint),
        ("Max Consecutive Shifts", check_max_cons_shifts_constraint),
        ("Max Weekend Days", check_max_weekend_days_constraint),
        ("Min Consecutive Days Off", check_min_cons_days_constraint),
        ("Min Consecutive Shifts", check_min_cons_shifts_constraint),
        ("Min/Max Worktime", check_min_max_worktime_constraint),
        ("Single Day Assignment", check_single_day_constraint),
        ("Shift Rotation", check_shift_rotation_constraint),
    ]


def _check_all_constraints(
    solution: "Solution",
) -> Tuple[bool, dict[str, tuple[bool, list[str]]]]:
    """
    Prüft alle Constraints und gibt Ergebnisse zurück.

    Returns:
        Tuple[bool, dict]: (alle_erfüllt, {constraint_name: (name,is_valid, violations)})
    """
    constraints = _get_all_constraint_checks()
    results: dict[str, tuple[bool, list[str]]] = {}
    all_valid = True

    for constraint_name, check_func in constraints:
        is_valid, violations = check_func(solution)
        results[constraint_name] = (is_valid, violations)
        if not is_valid:
            all_valid = False

    return all_valid, results