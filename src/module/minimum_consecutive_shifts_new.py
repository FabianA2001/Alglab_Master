from ortools.sat.python import cp_model

from .. import shift_vars
from ..inputTypes import instace
from .shift_assignment_module import ShiftAssignmentModule


class Minimum_consecutive_shifts_new(ShiftAssignmentModule):
    def build(
        self,
        instance: instace.Instance,
        vars: shift_vars.Shift_vars,
    ) -> cp_model.LinearExprT:
        for employee_uid in instance.employees:
            for day_s in range(1, 
                instance.employees[employee_uid].min_number_consecutive_shifts
            ):
                for day_d in range(instance.number_of_days - day_s - 1):
                    assigned_shifts = []
                    assigned_shifts_inner_interval = []
                    assigned_shifts_interval_end = []

                    assigned_shifts.append(vars.work_vars[(day_d, employee_uid)])
                    for day_j in range(day_d + 1, day_d + day_s + 1):
                        assigned_shifts_inner_interval.append(
                            vars.work_vars[(day_j, employee_uid)]
                        )
                    assigned_shifts_interval_end.append(
                        vars.work_vars[(day_d + day_s + 1, employee_uid)]
                    )
                    vars.model.add(
                        sum(assigned_shifts)
                        + day_s
                        - (sum(assigned_shifts_inner_interval))
                        + sum(assigned_shifts_interval_end)
                        > 0
                    )
        return 0


class Min_Cons_Shifts_Automaton(ShiftAssignmentModule):
    def build(self, instance, vars):
        for employee_uid in instance.employees:
            M = instance.employees[employee_uid].min_number_consecutive_shifts

            # Zustände:
            # 0       = off
            # 1..M    = on, Block läuft noch und hat Länge s
            # long    = M+2  = Block hat >= M erreicht (gültig)
            # fail    = M+1  = Fehlerzustand: irgendwo gab es einen zu kurzen Block (nicht akzeptierend)
            start = 0
            fail = M + 1
            long = M + 2

            # akzeptierende Endzustände: 0 (am Ende off), M (exakt min beendet), long (Block >= M beendet)
            accept = [0, M, long]

            transitions = []

            # state 0 (off)
            transitions.append((0, 0, 0))  # bleib off, wenn 0
            transitions.append((0, 1, 1))  # beginne neuen Block, wenn 1

            # states 1..M-1 (Block ist noch nicht lang genug)
            for s in range(1, M):
                transitions.append((s, 1, s + 1))  # wenn weiterarbeit (1) -> Länge +1
                transitions.append(
                    (s, 0, fail)
                )  # wenn 0 kommt -> zu kurzer Block -> Fehlerzustand

            # state M (genau Mindestlänge erreicht)
            transitions.append(
                (M, 1, long)
            )  # weiterarbeiten -> wird langer gültiger Block
            transitions.append(
                (M, 0, 0)
            )  # aufhören nach exakt M -> zurück zu off (gültig beendet)

            # state long (Block >= M, gültig)
            transitions.append((long, 1, long))  # weiterarbeiten -> bleib in long
            transitions.append(
                (long, 0, 0)
            )  # aufhören -> zurück zu off (gültig beendet)

            # fail state (einmal in fail -> für alle weiteren Eingaben in fail bleiben)
            transitions.append((fail, 0, fail))
            transitions.append((fail, 1, fail))

            sequence = [
                vars.work_vars[(day, employee_uid)]
                for day in range(instance.number_of_days)
            ]

            vars.model.AddAutomaton(sequence, start, accept, transitions)

        return 0

class Min_Cons_Shifts_Alternative_Enforce_If(ShiftAssignmentModule):
    def build(
        self,
        instance: instace.Instance,
        vars: shift_vars.Shift_vars,
    ) -> cp_model.LinearExprT:
        for employee_uid in instance.employees:
            minimal_consecutive = instance.employees[employee_uid].min_number_consecutive_shifts
            for day in range(instance.number_of_days - minimal_consecutive):
                for day_j in range(day + 1, day + minimal_consecutive):
                    vars.model.add(vars.get_work_vars(day_j, employee_uid)
                               <= vars.get_work_vars(day_j + 1, employee_uid)
                               ).OnlyEnforceIf(vars.get_work_vars(day, employee_uid).Not())
            
            day_s = 1
            for day in range(instance.number_of_days - minimal_consecutive, instance.number_of_days):
                for day_j in range(day + 1, day + minimal_consecutive - day_s):
                    vars.model.add(vars.get_work_vars(day_j, employee_uid)
                               <= vars.get_work_vars(day_j + 1, employee_uid)
                               ).OnlyEnforceIf(vars.get_work_vars(day - 1, employee_uid).Not())
                    day_s = day_s + 1
        return 0
    
class Min_Cons_Shifts_Alternative(ShiftAssignmentModule):
    def build(
        self,
        instance: instace.Instance,
        vars: shift_vars.Shift_vars,
    ) -> cp_model.LinearExprT:
        for employee_uid in instance.employees:
            minimal_consecutive = instance.employees[employee_uid].min_number_consecutive_shifts
            for day in range(instance.number_of_days - minimal_consecutive):
                for day_j in range(day + 1, day + minimal_consecutive):
                    vars.model.Add(vars.get_work_vars(day_j, employee_uid) 
                                   - vars.get_work_vars(day, employee_uid)
                                   <= vars.get_work_vars(day_j + 1, employee_uid)
                                   )
                    
            day_s = 1
            for day in range(instance.number_of_days - minimal_consecutive, instance.number_of_days):
                for day_j in range(day + 1, day + minimal_consecutive - day_s):
                    vars.model.add(vars.get_work_vars(day_j, employee_uid)
                                   - vars.get_work_vars(day, employee_uid)
                                   <= vars.get_work_vars(day_j + 1, employee_uid)
                                   )
                    day_s = day_s + 1
        return 0
    



# class Min_Cons_Shifts_Alternative(ShiftAssignmentModule):
#     def build(
#         self,
#         instance: instace.Instance,
#         vars: shift_vars.Shift_vars,
#     ) -> cp_model.LinearExprT:
#         for employee_uid in instance.employees:
#             minimal_consecutive = instance.employees[employee_uid].min_number_consecutive_shifts
#             for day in range(1, instance.number_of_days - minimal_consecutive):
#                 assigned_shifts_inner_interval = []
#                 for day_j in range(day, day + minimal_consecutive):
#                         assigned_shifts_inner_interval.append(
#                             vars.work_vars[(day_j, employee_uid)])
#                 # free day before and after interval?
#                 vars.model.add(vars.get_free_days_on_sides(day=day, employee_uid=employee_uid) 
#                                >= 1 - vars.work_vars[(day - 1, employee_uid)]
#                                - vars.work_vars[(day + minimal_consecutive, employee_uid)])
#                 # at least one working day inside interval
#                 vars.model.add(vars.get_work_days_in_interval(day=day, employee_uid=employee_uid)
#                                >= sum(assigned_shifts_inner_interval))
#                 vars.model.add(vars.get_work_days_in_interval(day=day, employee_uid=employee_uid)
#                                * vars.get_free_days_on_sides(day=day, employee_uid=employee_uid)
#                                * sum(assigned_shifts_inner_interval)
#                                == 
#                                vars.get_work_days_in_interval(day=day, employee_uid=employee_uid)
#                                * vars.get_free_days_on_sides(day=day, employee_uid=employee_uid)
#                                * minimal_consecutive)
#             # day_s = 1
#             # for day in range(instance.number_of_days - minimal_consecutive, instance.number_of_days - 1):
#             #     assigned_shifts_inner_interval = []
#             #     for day_j in range(day, day + minimal_consecutive - day_s):
#             #             assigned_shifts_inner_interval.append(
#             #                 vars.work_vars[(day_j, employee_uid)])
#             #     # free day before and after interval?
#             #     vars.model.add(vars.get_free_days_on_sides(day=day, employee_uid=employee_uid) 
#             #                    >= 1 - vars.work_vars[(day - 1, employee_uid)]
#             #                    - vars.work_vars[(day + minimal_consecutive - day_s, employee_uid)])
#             #     # at least one working day inside interval
#             #     vars.model.add(vars.get_work_days_in_interval(day=day, employee_uid=employee_uid)
#             #                    >= sum(assigned_shifts_inner_interval))
#             #     vars.model.add(vars.get_work_days_in_interval(day=day, employee_uid=employee_uid)
#             #                    * vars.get_free_days_on_sides(day=day, employee_uid=employee_uid)
#             #                    * sum(assigned_shifts_inner_interval)
#             #                    == 
#             #                    vars.get_work_days_in_interval(day=day, employee_uid=employee_uid)
#             #                    * vars.get_free_days_on_sides(day=day, employee_uid=employee_uid)
#             #                    * minimal_consecutive - day_s)
                
#         # TODO do something about the days after instance.number_of_days - instance.employees[employee_uid].min_number_consecutive_shifts
#         return 0
    