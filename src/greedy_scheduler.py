"""
Repaired + optimized Sequential Greedy Scheduler
"""

from collections import defaultdict
import math
from datetime import datetime

from ortools.sat.python import cp_model

from . import shift_vars
from .callback_early_stop import Callback_Early_Stop
from .inputTypes import instace
from .module import (
    assign_employee_day_shift,
    ban_employee_day_shift,
    cover_requirements,
    days_off_new,
    limited_shifts_per_type_validation,
    max_Cons_shifts_new,
    max_weekend_days,
    minimum_consecutive_shifts_new,
    minimum_consecutove_days_off_new,
    minMaxWorkTime,
    shift_assignment_single_day_validation,
    shift_rotation_constraint,
)
from .module.solverConstraints import SolverConstraints
from .solution import Solution


class SequentialGreedyScheduler:
    def __init__(self, instance: instace.Instance):
        self.instance = instance

        # x[(day, type_uid)] = [employee_uid, employee_uid, ...]
        self.x = defaultdict(list)

        # Per employee
        self.total_minutes = {emp: 0 for emp in instance.employees}
        self.shifts_per_type = {emp: defaultdict(int) for emp in instance.employees}
        self.last_shift_type = {emp: 0 for emp in instance.employees}

        # Coverage
        self.cover = defaultdict(int)

        # Precompute access for speed
        self.num_days = instance.number_of_days
        self.shift_types = instance.shift_types
        self.employees = instance.employees

        self.x = self.schedule()

    # ----------------------------------------------------------
    # HARD CONSTRAINTS + SCORE
    # ----------------------------------------------------------
    def greedy_score(self, emp, day, t):
        score = 0.0
        emp_obj = self.employees[emp]
        t_obj = self.shift_types[t]
        shift = self.instance.get_shift(day, t)

        # ---------- HARD CONSTRAINTS ----------

        # 1. Employee already assigned today
        for assigned_t in self.instance.shift_types:
            if emp in self.x[(day, assigned_t)]:
                return math.inf

        # 2. Day blocked
        if day in emp_obj.blocked_shifts:
            return math.inf

        # 3. Forbidden rotation: last_shift → t
        last = self.last_shift_type[emp]
        if last != 0:
            forbidden = self.shift_types[last].blocked_shifts_after
            if t in forbidden:
                return math.inf

        # 4. Max shifts of this type
        max_s = emp_obj.max_numbers_of_shifts.get(t, math.inf)
        if self.shifts_per_type[emp][t] >= max_s:
            return math.inf

        # 5. Max total minutes
        if self.total_minutes[emp] + t_obj.length > emp_obj.max_minutes_assigned:
            return math.inf

        max_cons = 1
        for i in range(emp_obj.max_number_consecutive_shifts):
            if day >= emp_obj.max_number_consecutive_shifts:
                for type_uid in self.instance.shift_types:
                    if self.x[(day - i, t)].count(emp) == 0:
                        max_cons = 0
        if max_cons == 1:
            return math.inf
        min_cons = 1
        for i in range(emp_obj.min_number_consecutive_shifts):
            if day >= emp_obj.min_number_consecutive_shifts:
                for type_uid in self.instance.shift_types:
                    if self.x[(day - i, t)].count(emp) == 0:
                        min_cons = 0
        if min_cons == 0:
            score = score - 1

        # days_off = 1
        # for i in range(emp_obj.min_number_consecutive_days_off):
        #     if day >= emp_obj.min_number_consecutive_days_off:
        #         for type_uid in self.instance.shift_types:
        #             if self.x[(day - i, t)].count(emp) > 0:
        #                 days_off = 0
        # if days_off == 0:
        #     return math.inf

        # ---------- SOFT CONSTRAINTS (Score) ----------
        # request on
        if self.instance.shifts[day][t].penalty_assigned_day_employee.get(emp, 0) > 0:
            score -= self.instance.shifts[day][t].penalty_assigned_day_employee[emp]
        # request off
        if (
            self.instance.shifts[day][t].penalty_not_assigned_day_employee.get(emp, 0)
            > 0
        ):
            score += self.instance.shifts[day][t].penalty_not_assigned_day_employee[emp]
        # A. reach minimum minutes
        if self.total_minutes[emp] < emp_obj.min_minutes_assigned:
            diff = emp_obj.min_minutes_assigned - self.total_minutes[emp]
            score += diff / 100.0

        # B. coverage
        current_cover = self.cover[(day, t)]
        desired = shift.preffert_number_employees

        if current_cover < desired:
            score += shift.weight_below_preferred * (
                desired - (desired - current_cover)
            )
        # else:
        #     score += shift.weight_above_preferred * (current_cover - desired)

        return score

    # ----------------------------------------------------------
    # SCHEDULING ALGORITHM (Sequential greedy)
    # ----------------------------------------------------------
    def schedule(self):
        """
        Verbesserter Greedy: Füllt jede Schicht iterativ mit mehreren Mitarbeitern bis zum Soll.
        """
        for day in range(self.num_days):
            for t in self.shift_types:
                shift = self.instance.get_shift(day, t)
                preferred = shift.preffert_number_employees
                assigned = set(self.x[(day, t)])
                # Versuche, bis zum Soll zu besetzen
                while len(assigned) < preferred:
                    best_emp = None
                    best_score = math.inf
                    for emp in self.employees:
                        if emp in assigned:
                            continue
                        s = self.greedy_score(emp, day, t)
                        if s < best_score:
                            best_score = s
                            best_emp = emp
                    if best_emp is None or best_score == math.inf:
                        break  # keine weiteren zulässig
                    # commit assignment
                    self.x[(day, t)].append(best_emp)
                    self.shifts_per_type[best_emp][t] += 1
                    self.total_minutes[best_emp] += self.shift_types[t].length
                    self.last_shift_type[best_emp] = t
                    self.cover[(day, t)] += 1
                    assigned.add(best_emp)
        return dict(self.x)

    # ----------------------------------------------------------
    # MATRIX EXPORT
    # ----------------------------------------------------------
    def get_assignment_matrix(self):
        """
        Return: dict[(day, type_uid, employee_uid)] = 1 if assigned, else 0 omitted
        Compact format: Only assigned entries stored as 1.
        """

        result = {}
        for day in range(self.instance.number_of_days):
            for type_uid in self.instance.shifts[day]:
                for employee_uid in self.instance.employees:
                    result[(day, type_uid, employee_uid)] = 0
        for (day, t), emps in self.x.items():
            for emp in emps:
                result[(day, t, emp)] = 1
        return result

    # small helpers
    def get_coverage(self):
        return dict(self.cover)

    def get_employee_statistics(self):
        stats = {}
        for emp in self.employees:
            stats[emp] = {
                "total_minutes": self.total_minutes[emp],
                "shifts_per_type": dict(self.shifts_per_type[emp]),
                "last_shift_type": self.last_shift_type[emp],
            }
        return stats
