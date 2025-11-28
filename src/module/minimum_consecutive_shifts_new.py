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
            for day_s in range(
                instance.employees[employee_uid].min_number_consecutive_shifts - 1
            ):
                for day_d in range(instance.number_of_days - (day_s + 1) - 1):
                    assigned_shifts = []
                    assigned_shifts_inner_interval = []
                    assigned_shifts_interval_end = []

                    assigned_shifts.append(vars.work_vars[(day_d, employee_uid)])
                    # Because range end range is exclusive, the end range should have + 1
                    # Because day_s start with 0, another +1 should be added
                    for day_j in range(day_d + 1, day_d + day_s + 1 + 1):
                        assigned_shifts_inner_interval.append(
                            vars.work_vars[(day_j, employee_uid)]
                        )
                    assigned_shifts_interval_end.append(
                        vars.work_vars[(day_d + day_s + 1 + 1, employee_uid)]
                    )
                    # Even though our indecies start with 0, day_s should still have the start value of 1
                    vars.model.add(
                        sum(assigned_shifts)
                        + day_s
                        + 1
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
