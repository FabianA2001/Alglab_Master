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
_solver_start_time: Optional[float] = None
_solver_end_time: Optional[float] = None
_solver_logs: list[str] = []
_solver_statistics: dict = {}
_last_objective_value: Optional[float] = None
_solver_status: Optional[str] = None


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


def set_solver_start_time(start_time: Optional[float]) -> None:
    """Setzt die Startzeit des Solvers.

    Args:
        start_time: Startzeit als Unix-Timestamp oder None
    """
    global _solver_start_time
    _solver_start_time = start_time


def get_solver_start_time() -> Optional[float]:
    """Holt die Startzeit des Solvers.

    Returns:
        Optional[float]: Startzeit als Unix-Timestamp oder None
    """
    return _solver_start_time


def set_solver_end_time(end_time: Optional[float]) -> None:
    """Setzt die Endzeit des Solvers.

    Args:
        end_time: Endzeit als Unix-Timestamp oder None
    """
    global _solver_end_time
    _solver_end_time = end_time


def get_solver_end_time() -> Optional[float]:
    """Holt die Endzeit des Solvers.

    Returns:
        Optional[float]: Endzeit als Unix-Timestamp oder None
    """
    return _solver_end_time


def get_solver_elapsed_time() -> Optional[float]:
    """Berechnet die verstrichene Solver-Zeit.

    Returns:
        Optional[float]: Verstrichene Zeit in Sekunden oder None
    """
    if _solver_start_time is None:
        return None
    if _solver_end_time is not None:
        return _solver_end_time - _solver_start_time
    import time

    return time.time() - _solver_start_time


def add_solver_log(log_message: str) -> None:
    """Fügt eine Log-Nachricht hinzu.

    Args:
        log_message: Die Log-Nachricht
    """
    global _solver_logs
    _solver_logs.append(log_message)


def get_solver_logs() -> list[str]:
    """Holt alle Solver-Logs.

    Returns:
        list[str]: Liste aller Log-Nachrichten
    """
    return _solver_logs.copy()


def clear_solver_logs() -> None:
    """Löscht alle Solver-Logs."""
    global _solver_logs
    _solver_logs = []


def set_solver_statistics(stats: dict) -> None:
    """Setzt Solver-Statistiken.

    Args:
        stats: Dictionary mit Statistiken
    """
    global _solver_statistics
    _solver_statistics = stats.copy()


def get_solver_statistics() -> dict:
    """Holt Solver-Statistiken.

    Returns:
        dict: Dictionary mit Statistiken
    """
    return _solver_statistics.copy()


def update_solver_statistics(key: str, value) -> None:
    """Aktualisiert einen Statistik-Wert.

    Args:
        key: Schlüssel der Statistik
        value: Wert der Statistik
    """
    global _solver_statistics
    _solver_statistics[key] = value


def set_last_objective_value(value: Optional[float]) -> None:
    """Setzt den letzten Objective Value.

    Args:
        value: Objective Value oder None
    """
    global _last_objective_value
    _last_objective_value = value


def get_last_objective_value() -> Optional[float]:
    """Holt den letzten Objective Value.

    Returns:
        Optional[float]: Objective Value oder None
    """
    return _last_objective_value


def set_solver_status(status: Optional[str]) -> None:
    """Setzt den Solver-Status.

    Args:
        status: Status-String (z.B. 'OPTIMAL', 'FEASIBLE', 'INFEASIBLE')
    """
    global _solver_status
    _solver_status = status


def get_solver_status() -> Optional[str]:
    """Holt den Solver-Status.

    Returns:
        Optional[str]: Status-String oder None
    """
    return _solver_status


def reset_solver_state() -> None:
    """Setzt alle Solver-bezogenen State-Variablen zurück."""
    global _solver_running, _solver_start_time, _solver_end_time
    global _solver_logs, _solver_statistics, _last_objective_value, _solver_status

    _solver_running = False
    _solver_start_time = None
    _solver_end_time = None
    _solver_logs = []
    _solver_statistics = {}
    _last_objective_value = None
    _solver_status = None
