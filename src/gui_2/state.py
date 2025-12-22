"""Zentrales State-Management für die GUI.

Dieses Modul verwaltet den globalen Zustand der Anwendung,
einschließlich aktueller Instance, Solution und Solver-Konfiguration.

Verwendet einfache globale Variablen für den Application State.
"""

from typing import Optional

from ..inputTypes.instace import Instance
from ..solution import Solution

# Globale Variablen für den Application State
_current_instance: Optional[Instance] = None
_current_solution: Optional[Solution] = None
_solver_running: bool = False


def set_instance(instance: Optional[Instance]) -> None:
    """Setzt die aktuelle Instance.

    Args:
        instance: Die neue Instance oder None
    """
    global _current_instance
    _current_instance = instance


def get_instance() -> Optional[Instance]:
    """Holt die aktuelle Instance.

    Returns:
        Optional[Instance]: Die aktuelle Instance oder None
    """
    return _current_instance


def set_solution(solution: Optional[Solution]) -> None:
    """Setzt die aktuelle Solution.

    Args:
        solution: Die neue Solution oder None
    """
    global _current_solution
    _current_solution = solution


def get_solution() -> Optional[Solution]:
    """Holt die aktuelle Solution.

    Returns:
        Optional[Solution]: Die aktuelle Solution oder None
    """
    return _current_solution


def set_solver_running(running: bool) -> None:
    """Setzt den Solver-Status.

    Args:
        running: True wenn Solver läuft, sonst False
    """
    global _solver_running
    _solver_running = running


def is_solver_running() -> bool:
    """Prüft ob der Solver läuft.

    Returns:
        bool: True wenn Solver läuft
    """
    return _solver_running
