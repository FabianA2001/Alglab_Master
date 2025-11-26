from ortools.sat.python import cp_model

from .. import shift_vars
from ..inputTypes import instace
from .shift_assignment_module import ShiftAssignmentModule


class Max_Cons_Shifts_new(ShiftAssignmentModule):
    def build(
        self,
        instance: instace.Instance,
        vars: shift_vars.Shift_vars,
    ) -> cp_model.LinearExprT:
        for employee_uid in instance.employees:
            for day in range(
                instance.number_of_days
                - instance.employees[employee_uid].max_number_consecutive_shifts
            ):
                assigned_shifts = []

                for i in range(
                    instance.employees[employee_uid].max_number_consecutive_shifts + 1
                ):
                    assigned_shifts.append(vars.work_vars[(day + i, employee_uid)])

                vars.model.Add(
                    sum(assigned_shifts)
                    <= instance.employees[employee_uid].max_number_consecutive_shifts
                )
        return 0


class Max_Cons_Shifts_Automaton(ShiftAssignmentModule):
    def build(self, instance, vars):
        for employee_uid in instance.employees:
            K = instance.employees[employee_uid].max_number_consecutive_shifts
            num_states = K + 2  # 0..K allowed, K+1 forbidden
            start = 0
            accept = list(range(K + 1))  # forbidden state is not accepted

            transitions = []
            for s in range(K + 1):
                # if work=1 → increase, but cap at K+1
                transitions.append((s, 1, min(s + 1, K + 1)))
                # if work=0 → reset
                transitions.append((s, 0, 0))

            # forbidden state loops to itself on both symbols
            transitions.append((K + 1, 0, K + 1))
            transitions.append((K + 1, 1, K + 1))

            sequence = [
                vars.work_vars[(day, employee_uid)]
                for day in range(instance.number_of_days)
            ]

            vars.model.AddAutomaton(sequence, start, accept, transitions)

        return 0
