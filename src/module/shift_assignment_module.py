import abc

from ortools.sat.python import cp_model

from .. import shift_vars
from ..inputTypes import instace


class ShiftAssignmentModule(abc.ABC):
    @abc.abstractmethod
    def build(
        self,
        instance: instace.Instance,
        vars: shift_vars.Shift_vars,
    ) -> cp_model.LinearExprT:
        return 0
