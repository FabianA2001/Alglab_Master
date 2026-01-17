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


class callback_until_objective_value(cp_model.CpSolverSolutionCallback):
    def __init__(self, desired_objective_value):
        super().__init__()
        self.desired_objective_value = desired_objective_value

    def on_solution_callback(self):
        if self.objective_value <= self.desired_objective_value:
            self.StopSearch()
