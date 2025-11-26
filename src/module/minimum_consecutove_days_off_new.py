from ortools.sat.python import cp_model

from .. import shift_vars
from ..inputTypes import instace
from .shift_assignment_module import ShiftAssignmentModule


class Minimum_consecutive_days_off_new(ShiftAssignmentModule):
    def build(
        self,
        instance: instace.Instance,
        vars: shift_vars.Shift_vars,
    ) -> cp_model.LinearExprT:
        for employee_uid in instance.employees:
            # TODO is a constraint with 1 consecutive working day meaningful?
            for day_s in range(
                instance.employees[employee_uid].min_number_consecutive_days_off - 1
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
                    vars.model.add(
                        1
                        - (sum(assigned_shifts))
                        + sum(assigned_shifts_inner_interval)
                        + 1
                        - (sum(assigned_shifts_interval_end))
                        > 0
                    )
        return 0


class Min_Cons_Days_Off_Automaton(ShiftAssignmentModule):
    def build(self, instance, vars):
        for employee_uid in instance.employees:
            D = instance.employees[employee_uid].min_number_consecutive_days_off

            # Zustände:
            # 0       = working
            # 1..D    = off, aber noch nicht lang genug
            # long    = D+2   = gültiger langer off-block (>=D)
            # fail    = D+1   = Fehlerzustand: ein off-block war zu kurz

            start = 0
            fail = D + 1
            long = D + 2

            # akzeptierende Endzustände:
            # 0 (endet arbeitend)
            # D (genau D Tage off und dann wieder arbeit)
            # long (langer Off-Block >=D)
            accept = [0, D, long]

            transitions = []

            # working
            transitions.append((0, 1, 0))  # arbeitet weiter
            transitions.append((0, 0, 1))  # beginnt off-block

            # states 1..D-1 (Off-Block, noch zu kurz)
            for s in range(1, D):
                transitions.append((s, 0, s + 1))  # off-block wächst
                transitions.append((s, 1, fail))  # Ende zu früh -> Fehler

            # state D (genau D Off-Tage erreicht)
            transitions.append((D, 0, long))  # längerer off-block
            transitions.append((D, 1, 0))  # genau D -> off-block endet gültig

            # long off block (>=D)
            transitions.append((long, 0, long))  # weiter off
            transitions.append((long, 1, 0))  # gültig beendet

            # fail state (einmal fail -> immer fail)
            transitions.append((fail, 0, fail))
            transitions.append((fail, 1, fail))

            sequence = [
                1 - vars.work_vars[(day, employee_uid)]  # OFF=1, WORK=0
                for day in range(instance.number_of_days)
            ]

            vars.model.AddAutomaton(sequence, start, accept, transitions)

        return 0
