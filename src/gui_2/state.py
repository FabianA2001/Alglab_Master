"""Zentrales State-Management für die GUI.

Dieses Modul verwaltet den globalen Zustand der Anwendung,
einschließlich aktueller Instance, Solution und Solver-Konfiguration.

Verwendet einfache globale Variablen für den Application State.
"""

from typing import Optional

from ..inputTypes.instace import Instance
from ..solution import Solution

#####
"""
WICHTIGER HINWEIS:
varibalen in der reseter funktion hinzufügen, damit diese zurückgesetzt werden können.
"""
#####

# Globale Variablen für den Application State
_current_instance: Optional[Instance] = None
_current_solution: list[Solution] = []
_solver_running: bool = False
_solver_start_time: Optional[float] = None
_solver_end_time: Optional[float] = None
_solver_logs: list[str] = []
_solver_statistics: dict = {}
_last_objective_value: Optional[float] = None
_solver_status: Optional[str] = None
_changed_days: set[int] = set()
_solver_timeout: float | None = None  # Default timeout in Sekunden

# UI-Referenzen (für Background-Updates)
solver_log_html_element = None
solver_log_scroll_area = None
solver_runtime_task = None


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


def add_solution(solution: Solution) -> None:
    """Setzt die aktuelle Solution.

    Args:
        solution: Die neue Solution oder None
    """
    global _current_solution
    clear_changed_days()
    _current_solution.append(solution)


def clear_solutions():
    """Löscht alle gespeicherten Solutions."""
    global _current_solution
    clear_changed_days()
    _current_solution = []


def get_solution() -> Optional[Solution]:
    """Holt die aktuelle Solution.

    Returns:
        Optional[Solution]: Die aktuelle Solution oder None
    """
    if len(_current_solution) == 0:
        return None
    return _current_solution[-1]


def get_all_solutions() -> list[Solution]:
    """Holt alle gespeicherten Solutions.

    Returns:
        Optional[list[Solution]]: Liste aller Solutions oder None
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

    Speichert maximal die letzten 1000 Log-Einträge.

    Args:
        log_message: Die Log-Nachricht
    """
    global _solver_logs
    _solver_logs.append(log_message)
    # Behalte nur die letzten 1000 Einträge
    if len(_solver_logs) > 1000:
        _solver_logs = _solver_logs[-1000:]


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


def set_changed_days(days: set[int]) -> None:
    """Setzt die geänderten Tage für LNS minimal changes.

    Args:
        days: Set mit Tages-Indizes die geändert wurden
    """
    global _changed_days
    _changed_days = days.copy()


def get_changed_days() -> set[int]:
    """Holt die geänderten Tage.

    Returns:
        set[int]: Set mit Tages-Indizes die geändert wurden
    """
    return _changed_days.copy()


def add_changed_day(day: int) -> None:
    """Fügt einen geänderten Tag hinzu.

    Args:
        day: Tages-Index der hinzugefügt werden soll
    """
    global _changed_days
    _changed_days.add(day)


def clear_changed_days() -> None:
    """Löscht alle geänderten Tage."""
    global _changed_days
    _changed_days = set()


def set_solver_timeout(timeout: float) -> None:
    """Setzt das Solver-Timeout.

    Args:
        timeout: Timeout in Sekunden
    """
    global _solver_timeout
    _solver_timeout = max(1.0, timeout)  # Mindestens 1 Sekunde


def get_solver_timeout() -> float | None:
    """Holt das Solver-Timeout.

    Returns:
        float: Timeout in Sekunden
    """
    return _solver_timeout


def rest_solutions() -> None:
    clear_changed_days()
    clear_solutions()


def reset_solver_state() -> None:
    """Setzt alle Solver-bezogenen State-Variablen zurück."""
    global _solver_running, _solver_start_time, _solver_end_time
    global _solver_logs, _solver_statistics, _last_objective_value, _solver_status
    global solver_log_html_element, solver_log_scroll_area, solver_runtime_task
    # Hinweis: _solver_timeout wird NICHT zurückgesetzt, da es eine Benutzereinstellung ist

    _solver_running = False
    _solver_start_time = None
    _solver_end_time = None
    _solver_logs = []
    _solver_statistics = {}
    _last_objective_value = None
    _solver_status = None

    # Stoppe Runtime-Task falls vorhanden
    if solver_runtime_task is not None:
        try:
            solver_runtime_task.cancel()
        except:
            print("Fehler beim Abbrechen der Solver-Runtime-Task.")
            pass

    solver_log_html_element = None
    solver_log_scroll_area = None
    solver_runtime_task = None
