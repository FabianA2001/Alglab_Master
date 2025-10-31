from typing import Dict, Tuple

from pydantic import BaseModel, Field

from .inputTypes import employee, instace, shift

import string


class Solution(BaseModel):
    def __init__(self, instance: instace.Instance, **data):
        super().__init__(instance=instance, **data)

    """Class to handle variable storage and management for shift scheduling."""

    vars: Dict[Tuple[int, shift.ShiftUid, employee.EmployeeUid], int] = Field(
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

    def set_var(self, day: int, type_uid: int, employee_uid: int, value: int):
        """Sets the boolean variable value."""
        self.vars[(day, type_uid, employee_uid)] = value

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
                f"weekend_work_{list(self.instance.weekend_days)[weekend]}_for_{self.instance.employees[employee_uid].name}: ",
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
