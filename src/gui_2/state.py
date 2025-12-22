"""Zentrales State-Management für die GUI.

Dieses Modul verwaltet den globalen Zustand der Anwendung,
einschließlich aktueller Instance, Solution und Solver-Konfiguration.
"""

from enum import Enum
from typing import Optional

from nicegui import app

from ..inputTypes.instace import Instance
from ..solution import Solution


class StateKey(Enum):
    """Enum für State-Schlüssel mit Default-Werten."""

    APP_STATE = None
    CURRENT_INSTANCE = None
    CURRENT_SOLUTION = None
    SOLVER_RUNNING = False


def get_app_state():
    """Holt oder erstellt den globalen AppState im general storage.

    Returns:
        dict: Der globale Anwendungszustand
    """
    if StateKey.APP_STATE not in app.storage.general:
        app.storage.general[StateKey.APP_STATE] = {
            key: key.value for key in StateKey if key != StateKey.APP_STATE
        }
    return app.storage.general[StateKey.APP_STATE]


def set_instance(instance: Optional[Instance]) -> None:
    """Setzt die aktuelle Instance.

    Args:
        instance: Die neue Instance oder None
    """
    state = get_app_state()
    state[StateKey.CURRENT_INSTANCE] = instance


def get_instance() -> Optional[Instance]:
    """Holt die aktuelle Instance.

    Returns:
        Optional[Instance]: Die aktuelle Instance oder None
    """
    state = get_app_state()
    return state.get(StateKey.CURRENT_INSTANCE, StateKey.CURRENT_INSTANCE.value)


def set_solution(solution: Optional[Solution]) -> None:
    """Setzt die aktuelle Solution.

    Args:
        solution: Die neue Solution oder None
    """
    state = get_app_state()
    state[StateKey.CURRENT_SOLUTION] = solution


def get_solution() -> Optional[Solution]:
    """Holt die aktuelle Solution.

    Returns:
        Optional[Solution]: Die aktuelle Solution oder None
    """
    state = get_app_state()
    return state.get(StateKey.CURRENT_SOLUTION, StateKey.CURRENT_SOLUTION.value)


def set_solver_running(running: bool) -> None:
    """Setzt den Solver-Status.

    Args:
        running: True wenn Solver läuft, sonst False
    """
    state = get_app_state()
    state[StateKey.SOLVER_RUNNING] = running


def is_solver_running() -> bool:
    """Prüft ob der Solver läuft.

    Returns:
        bool: True wenn Solver läuft
    """
    state = get_app_state()
    return state.get(StateKey.SOLVER_RUNNING, StateKey.SOLVER_RUNNING.value)
