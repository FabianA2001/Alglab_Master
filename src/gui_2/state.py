"""Zentrales State-Management für die GUI.

Dieses Modul verwaltet den globalen Zustand der Anwendung,
einschließlich aktueller Instance, Solution und Solver-Konfiguration.
"""

from typing import Optional

from nicegui import app, ui

from ..inputTypes.instace import Instance
from ..solution import Solution


def get_app_state():
    """Holt oder erstellt den globalen AppState im general storage.

    Returns:
        dict: Der globale Anwendungszustand
    """
    if "app_state" not in app.storage.general:
        app.storage.general["app_state"] = {
            "current_instance": None,
            "current_solution": None,
            "solver_running": False,
        }
    return app.storage.general["app_state"]


def set_instance(instance: Optional[Instance]) -> None:
    """Setzt die aktuelle Instance.

    Args:
        instance: Die neue Instance oder None
    """
    state = get_app_state()
    state["current_instance"] = instance
    ui.notify(f"Instance im State gesetzt: {instance is not None}", type="info")


def get_instance() -> Optional[Instance]:
    """Holt die aktuelle Instance.

    Returns:
        Optional[Instance]: Die aktuelle Instance oder None
    """
    state = get_app_state()
    return state.get("current_instance")


def set_solution(solution: Optional[Solution]) -> None:
    """Setzt die aktuelle Solution.

    Args:
        solution: Die neue Solution oder None
    """
    state = get_app_state()
    state["current_solution"] = solution


def get_solution() -> Optional[Solution]:
    """Holt die aktuelle Solution.

    Returns:
        Optional[Solution]: Die aktuelle Solution oder None
    """
    state = get_app_state()
    return state.get("current_solution")


def set_solver_running(running: bool) -> None:
    """Setzt den Solver-Status.

    Args:
        running: True wenn Solver läuft, sonst False
    """
    state = get_app_state()
    state["solver_running"] = running


def is_solver_running() -> bool:
    """Prüft ob der Solver läuft.

    Returns:
        bool: True wenn Solver läuft
    """
    state = get_app_state()
    return state.get("solver_running", False)
