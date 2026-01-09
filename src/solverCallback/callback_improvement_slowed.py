from datetime import datetime

from ortools.sat.python import cp_model
from pydantic import BaseModel, Field
from typing import List, Tuple, Set

from .. import shift_vars
from ..inputTypes import instace
from ..module import (
    cover_requirements,
    days_off,
    limited_shifts_per_type_validation,
    max_Cons_Shifts,
    max_weekend_days,
    minimum_consecutive_days_off,
    minimum_consecutive_shifts,
    minMaxWorkTime,
    shift_assignment_single_day_validation,
    shift_rotation_constraint,
)
from ..module.solverConstraints import SolverConstraints
from ..solution import Solution
import time


class callback_improvement_slowed(cp_model.CpSolverSolutionCallback):
    def __init__(self, time_between_checks_in_seconds:int=30, percentual_improvement:float=0, numerical_improvement:int=0):
        """
        A callback that stop the solver if a wanted improvement is not met every "time_between_checks_in_seconds" seconds.
        If no improvement is given the callback will never stop the solver.
        If both percentual_improvement and numerical_improvement are given they both should succesed or else the solver stop.
        
        :param self: Description
        :param time_between_checks_in_seconds: Time between checks
        :type time_between_checks_in_seconds: int
        :param percentual_improvement: The improvement required for the check to succesed should be between [0, 1]
        :type percentual_improvement: float
        :param numerical_improvement: The improvement required for the check to succesed
        :type numerical_improvement: int
        """
        super().__init__()
        self.time_between_checks_in_seconds = time_between_checks_in_seconds
        self.percentual_improvement = percentual_improvement
        self.numerical_improvement = numerical_improvement
        self.last_check_time = time.time()
        self.last_check_objective_value = float('inf')
    
    def on_solution_callback(self):
        if time.time() - self.last_check_time >= self.time_between_checks_in_seconds and (self.percentual_improvement > 0 or self.numerical_improvement > 0):
            self.last_check_time = time.time()
            print(time.time() - self.last_check_time)
            print(self.time_between_checks_in_seconds)
            print(self.last_check_objective_value - self.numerical_improvement, ">=", self.objective_value)
            print(self.last_check_objective_value * (1 - self.percentual_improvement), ">=", self.objective_value)
            if not (self.last_check_objective_value - self.numerical_improvement >= self.objective_value and self.last_check_objective_value * (1 - self.percentual_improvement) >= self.objective_value):
                self.StopSearch()
            else:
                self.last_check_objective_value=self.objective_value