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
            for day_s in range(1,
                instance.employees[employee_uid].min_number_consecutive_days_off
            ):
                for day_d in range(instance.number_of_days - day_s - 1):
                    assigned_shifts = []
                    assigned_shifts_inner_interval = []
                    assigned_shifts_interval_end = []

                    assigned_shifts.append(vars.work_vars[(day_d, employee_uid)])
                    # Because range end range is exclusive, the end range should have + 1
                    # Because day_s start with 0, another +1 should be added
                    for day_j in range(day_d + 1, day_d + day_s + 1):
                        assigned_shifts_inner_interval.append(
                            vars.work_vars[(day_j, employee_uid)]
                        )
                    assigned_shifts_interval_end.append(
                        vars.work_vars[(day_d + day_s + 1, employee_uid)]
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

            # Sonderfall: kein Minimum -> nichts zu erzwingen
            if D <= 0:
                continue

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
            # D (exakt D Off-Tage erreicht und dann wieder Arbeit)
            # long (langer Off-Block >=D)
            accept = [0, D, long]

            transitions = []

            # working-state 0:

            transitions.append((0, 1, 0))  # weiter arbeiten
            transitions.append((0, 0, 1))  # beginne off-block

            # states 1..D-1 (Off-Block, noch zu kurz)

            for s in range(1, D):
                transitions.append((s, 0, s + 1))  # off-block wächst
                transitions.append((s, 1, fail))  # zu früh wieder arbeiten -> Fehler

            # state D (genau D Off-Tage erreicht)

            transitions.append((D, 0, long))
            transitions.append((D, 1, 0))

            # long off block (>=D)

            transitions.append((long, 0, long))
            transitions.append((long, 1, 0))

            # fail state (einmal fail -> immer fail)
            transitions.append((fail, 0, fail))
            transitions.append((fail, 1, fail))

            sequence = [
                vars.work_vars[(day, employee_uid)]
                for day in range(instance.number_of_days)
            ]

            vars.model.AddAutomaton(sequence, start, accept, transitions)

        return 0




class Min_Cons_Days_Off_Alternative_Enforce_If(ShiftAssignmentModule):
    def build(
        self,
        instance: instace.Instance,
        vars: shift_vars.Shift_vars,
    ) -> cp_model.LinearExprT:
        for employee_uid in instance.employees:
            minimal_consecutive = instance.employees[employee_uid].min_number_consecutive_days_off
            for day in range(instance.number_of_days - minimal_consecutive):
                for day_j in range(day + 1, day + minimal_consecutive):
                    vars.model.add(vars.get_work_vars(day_j, employee_uid)
                               >= vars.get_work_vars(day_j + 1, employee_uid)
                               ).OnlyEnforceIf(vars.get_work_vars(day, employee_uid))
        return 0
    
class Min_Cons_Days_Off_Alternative(ShiftAssignmentModule):
    def build(
        self,
        instance: instace.Instance,
        vars: shift_vars.Shift_vars,
    ) -> cp_model.LinearExprT:
        for employee_uid in instance.employees:
            minimal_consecutive = instance.employees[employee_uid].min_number_consecutive_days_off
            for day in range(instance.number_of_days - minimal_consecutive):
                for day_j in range(day + 1, day + minimal_consecutive):
                    vars.model.add(vars.get_work_vars(day_j, employee_uid) 
                                   + ( 1 - vars.get_work_vars(day, employee_uid))
                                   >= vars.get_work_vars(day_j + 1, employee_uid)
                                   )
        return 0
    

class Min_Cons_Days_Off_Alternative_exact_Enforce_If(ShiftAssignmentModule):
    def build(
        self,
        instance: instace.Instance,
        vars: shift_vars.Shift_vars,
    ) -> cp_model.LinearExprT:
        for employee_uid in instance.employees:
            minimal_consecutive = instance.employees[employee_uid].min_number_consecutive_days_off
            for day in range(instance.number_of_days - minimal_consecutive):
                for day_j in range(day + 1, day + minimal_consecutive):
                    vars.model.add(vars.get_work_vars(day_j, employee_uid)
                               >= vars.get_work_vars(day_j + 1, employee_uid)
                               ).OnlyEnforceIf(vars.get_work_vars(day, employee_uid)
                                               , vars.get_work_vars(day + 1, employee_uid).Not())
            
            # Constraint for days that do not have less than minimal_consecutive days after them
            day_s = 1
            for day in range(instance.number_of_days - minimal_consecutive, instance.number_of_days):
                for day_j in range(day + 1, day + minimal_consecutive - day_s):
                    vars.model.add(vars.get_work_vars(day_j, employee_uid)
                               >= vars.get_work_vars(day_j + 1, employee_uid)
                               ).OnlyEnforceIf(vars.get_work_vars(day, employee_uid)
                                               , vars.get_work_vars(day + 1, employee_uid).Not())
                day_s = day_s + 1
        return 0
    
class Min_Cons_Days_Off_Alternative_exact(ShiftAssignmentModule):
    def build(
        self,
        instance: instace.Instance,
        vars: shift_vars.Shift_vars,
    ) -> cp_model.LinearExprT:
        for employee_uid in instance.employees:
            minimal_consecutive = instance.employees[employee_uid].min_number_consecutive_days_off
            for day in range(instance.number_of_days - minimal_consecutive):
                for day_j in range(day + 1, day + minimal_consecutive):
                    vars.model.add(vars.get_work_vars(day_j, employee_uid) 
                                   + ( 1 - vars.get_work_vars(day, employee_uid))
                                   + vars.get_work_vars(day + 1, employee_uid)
                                   >= vars.get_work_vars(day_j + 1, employee_uid)
                                   )
                    
            # Constraint for days that do not have less than minimal_consecutive days after them
            day_s = 1
            for day in range(instance.number_of_days - minimal_consecutive, instance.number_of_days):
                for day_j in range(day + 1, day + minimal_consecutive - day_s):
                    vars.model.add(vars.get_work_vars(day_j, employee_uid) 
                                   + ( 1 - vars.get_work_vars(day, employee_uid))
                                   + vars.get_work_vars(day + 1, employee_uid)
                                   >= vars.get_work_vars(day_j + 1, employee_uid)
                                   )
                day_s = day_s + 1
        return 0




class Min_Cons_Days_Off_Alternative_exact_original(ShiftAssignmentModule):
    def build(
        self,
        instance: instace.Instance,
        vars: shift_vars.Shift_vars,
    ) -> cp_model.LinearExprT:
        for employee_uid in instance.employees:
            minimal_consecutive = instance.employees[employee_uid].min_number_consecutive_days_off
            for day in range(instance.number_of_days - minimal_consecutive):
                for day_j in range(day + 1, day + minimal_consecutive):
                    assigned_shifts_start = []
                    assigned_shifts_end = []
                    assigned_shifts_inner_interval = []
                    assigned_shifts_interval_end = []
                    for type_uid in instance.shift_types:
                        assigned_shifts_start.append(
                            vars.vars[(day_j, type_uid, employee_uid)]
                        )
                        assigned_shifts_end.append(
                            vars.vars[(day, type_uid, employee_uid)]
                        )
                        assigned_shifts_inner_interval.append(
                            vars.vars[(day + 1, type_uid, employee_uid)]
                        )
                        assigned_shifts_interval_end.append(
                            vars.vars[(day_j + 1, type_uid, employee_uid)]
                        )
                    vars.model.add(sum(assigned_shifts_start)
                                   + ( 1 - sum(assigned_shifts_end))
                                   + sum(assigned_shifts_inner_interval)
                                   >= sum(assigned_shifts_interval_end)
                                   )
                    
            # Constraint for days that do not have less than minimal_consecutive days after them
            day_s = 1
            for day in range(instance.number_of_days - minimal_consecutive, instance.number_of_days):
                for day_j in range(day + 1, day + minimal_consecutive - day_s):
                    assigned_shifts_start = []
                    assigned_shifts_end = []
                    assigned_shifts_inner_interval = []
                    assigned_shifts_interval_end = []
                    for type_uid in instance.shift_types:
                        assigned_shifts_start.append(
                            vars.vars[(day_j, type_uid, employee_uid)]
                        )
                        assigned_shifts_end.append(
                            vars.vars[(day, type_uid, employee_uid)]
                        )
                        assigned_shifts_inner_interval.append(
                            vars.vars[(day + 1, type_uid, employee_uid)]
                        )
                        assigned_shifts_interval_end.append(
                            vars.vars[(day_j + 1, type_uid, employee_uid)]
                        )
                    vars.model.add(sum(assigned_shifts_start)
                                   + ( 1 - sum(assigned_shifts_end))
                                   + sum(assigned_shifts_inner_interval)
                                   >= sum(assigned_shifts_interval_end)
                                   )
                day_s = day_s + 1
        return 0
    

class Min_Cons_Days_Off_Alternative_Enforce_If_original(ShiftAssignmentModule):
    def build(
        self,
        instance: instace.Instance,
        vars: shift_vars.Shift_vars,
    ) -> cp_model.LinearExprT:
        for employee_uid in instance.employees:
            minimal_consecutive = instance.employees[employee_uid].min_number_consecutive_days_off
            for day in range(instance.number_of_days - minimal_consecutive):
                for day_j in range(day + 1, day + minimal_consecutive):
                    assigned_shifts_start = []
                    assigned_shifts_end = []
                    assigned_shifts_interval_end = []
                    for type_uid in instance.shift_types:
                        assigned_shifts_start.append(
                            vars.vars[(day_j, type_uid, employee_uid)]
                        )
                        assigned_shifts_end.append(
                            vars.vars[(day, type_uid, employee_uid)]
                        )
                        assigned_shifts_interval_end.append(
                            vars.vars[(day_j + 1, type_uid, employee_uid)]
                        )
                    vars.model.add(sum(assigned_shifts_start)
                               >= sum(assigned_shifts_interval_end)
                               ).OnlyEnforceIf(assigned_shifts_end)
        return 0