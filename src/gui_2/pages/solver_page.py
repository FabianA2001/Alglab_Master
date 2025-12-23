"""Solver-Seite für die GUI.

Bietet eine Benutzeroberfläche zur Konfiguration und Ausführung
verschiedener Solver-Methoden mit Echtzeit-Logging und Laufzeitanzeige.
"""

import asyncio
import sys
import threading
import time
from datetime import datetime
from io import StringIO
from typing import Any

from nicegui import ui

from ...shift_vars import Shift_vars
from ...solver import Solver
from .. import state

# Konstanten
LOG_SEPARATOR = "─" * 60
MAX_LOG_LINES = 50
DEFAULT_TIMEOUT_SECONDS = 300.0
RUNTIME_UPDATE_INTERVAL = 0.1


def solver_page() -> None:
    """Seite für Solver-Konfiguration und -Ausführung."""

    # Lokale State-Variablen
    solver_thread: threading.Thread | None = None
    log_buffer: list[str] = []
    start_time: float | None = None
    is_running: bool = False

    # Konfiguration der verfügbaren Solver-Methoden
    solver_methods = [
        {
            "name": "Standard Solve",
            "description": "Standard CP-SAT Solver",
            "icon": "play_arrow",
            "method": "solve",
            "color": "positive",
            "params": {
                "log_search_progress": False,
                "max_time_in_seconds": DEFAULT_TIMEOUT_SECONDS,
            },
        },
        {
            "name": "Solve mit Early Stop",
            "description": "Solver mit Early-Stop-Callback",
            "icon": "fast_forward",
            "method": "solve_with_early_stop",
            "color": "primary",
            "params": {
                "log_search_progress": False,
                "max_time_in_seconds": DEFAULT_TIMEOUT_SECONDS,
            },
        },
        {
            "name": "Erste Lösung",
            "description": "Stoppt nach erster gefundener Lösung",
            "icon": "looks_one",
            "method": "solve",
            "color": "secondary",
            "params": {
                "log_search_progress": False,
                "max_time_in_seconds": 60.0,
                "stop_after_first_solution": True,
            },
        },
    ]

    @ui.refreshable
    def instance_info() -> None:
        """Zeigt die Instance-Informationen an."""
        current_instance = state.get_instance()
        if current_instance:
            num_employees = len(current_instance.employees)
            num_shift_types = len(current_instance.shift_types)
            num_days = current_instance.number_of_days
            ui.label(
                f"✓ Instance geladen: {num_employees} Mitarbeiter, "
                f"{num_shift_types} Schichttypen, "
                f"{num_days} Tage"
            ).classes("text-green-600")
        else:
            ui.label("✗ Keine Instance geladen").classes("text-orange-500")

    @ui.refreshable
    def solution_info() -> None:
        """Zeigt die Solution-Informationen an."""
        current_solution = state.get_solution()
        if current_solution:
            objective = current_solution.objective_value
            ui.label(f"✓ Solution vorhanden (Objective: {objective:.2f})").classes(
                "text-blue-600"
            )
        else:
            ui.label("✗ Keine Solution vorhanden").classes("text-gray-500")

    @ui.refreshable
    def runtime_display() -> None:
        """Zeigt die Laufzeit an."""
        elapsed_time = state.get_solver_elapsed_time()
        if elapsed_time is not None:
            minutes = int(elapsed_time // 60)
            seconds = elapsed_time % 60
            display_text = f"Laufzeit: {minutes}m {seconds:.1f}s"
        else:
            display_text = "Laufzeit: 0m 0.0s"
        ui.label(display_text).classes("text-xl font-bold")

    @ui.refreshable
    def log_display() -> None:
        """Zeigt die Solver-Logs an."""
        logs = state.get_solver_logs()
        recent_logs = logs[-MAX_LOG_LINES:]
        with ui.scroll_area().classes("w-full h-96 bg-gray-100 p-4 font-mono text-sm"):
            ui.html("<pre>" + "\n".join(recent_logs) + "</pre>", sanitize=False)

    @ui.refreshable
    def control_buttons() -> None:
        """Zeigt die Steuerungs-Buttons an."""
        can_start = state.get_instance() is not None and not state.is_solver_running()
        is_solver_active = state.is_solver_running()

        with ui.column().classes("w-full gap-4"):
            # Solver-Methoden Buttons
            ui.label("Solver-Methoden").classes("text-lg font-bold")
            with ui.grid(columns=3).classes("w-full gap-2"):
                for method_config in solver_methods:
                    button = ui.button(
                        method_config["name"],
                        icon=method_config["icon"],
                        on_click=lambda e, m=method_config: start_solver(m),
                    )
                    if can_start:
                        button.props(f"color={method_config['color']}")
                    button.set_enabled(can_start)
                    button.tooltip(method_config["description"])

            # Stop Button separat
            ui.separator()
            ui.button(
                "Solver stoppen",
                icon="stop",
                on_click=stop_solver,
            ).props("color=negative").set_enabled(is_solver_active)

    def add_log_message(message: str) -> None:
        """Fügt eine Log-Nachricht mit Zeitstempel hinzu.

        Args:
            message: Die zu loggende Nachricht
        """
        nonlocal log_buffer
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        log_buffer.append(log_entry)
        state.add_solver_log(log_entry)
        log_display.refresh()

    async def runtime_updater() -> None:
        """Aktualisiert die Laufzeitanzeige kontinuierlich."""
        while is_running:
            runtime_display.refresh()
            await asyncio.sleep(RUNTIME_UPDATE_INTERVAL)

    class TeeOutput:
        """Schreibt Output gleichzeitig in stdout und Log.

        Ermöglicht das Erfassen von Solver-Logs ohne
        die normale Konsolenausgabe zu unterdrücken.
        """

        def __init__(self, original_stdout, buffer: StringIO) -> None:
            """Initialisiert den TeeOutput.

            Args:
                original_stdout: Der ursprüngliche stdout-Stream
                buffer: StringIO-Buffer für erfassten Output
            """
            self.original_stdout = original_stdout
            self.buffer = buffer

        def write(self, text: str) -> None:
            """Schreibt Text in beide Streams.

            Args:
                text: Der zu schreibende Text
            """
            self.original_stdout.write(text)
            self.buffer.write(text)
            if text.strip():
                add_log_message(text.rstrip())

        def flush(self) -> None:
            """Flusht beide Streams."""
            self.original_stdout.flush()
            self.buffer.flush()

    def solve_in_thread(method_config: dict[str, Any]) -> None:
        """Führt den Solver in einem separaten Thread aus.

        Args:
            method_config: Dictionary mit Methoden-Konfiguration
                - name: Anzeigename der Methode
                - method: Name der Solver-Methode
                - params: Parameter für die Solver-Methode
        """
        nonlocal is_running, start_time

        # Erstelle stdout-Umleitung
        stdout_buffer = StringIO()
        old_stdout = sys.stdout

        try:
            instance = state.get_instance()
            if not instance:
                add_log_message("❌ Keine Instance geladen!")
                return

            # Log Start-Informationen
            add_log_message("🚀 Starte Solver...")
            add_log_message(f"Methode: {method_config['name']}")
            add_log_message(
                f"Instance: {len(instance.employees)} Mitarbeiter, "
                f"{instance.number_of_days} Tage"
            )

            # Speichere Instance-Statistiken
            _save_instance_statistics(instance, method_config)

            # Erstelle Variablen und Solver
            vars = Shift_vars(instance)
            solver = Solver(instance, vars)

            add_log_message("⚙️ Solver initialisiert")
            add_log_message(f"🔍 Suche nach Lösung mit: {method_config['method']}...")
            add_log_message(LOG_SEPARATOR)

            # Leite stdout um für Solver-Logs
            sys.stdout = TeeOutput(old_stdout, stdout_buffer)

            # Führe Solver-Methode aus
            solver_method = getattr(solver, method_config["method"])
            solution = solver_method(**method_config["params"])

            # Stelle stdout wieder her
            sys.stdout = old_stdout

            # Speichere Ergebnisse (start_time ist garantiert nicht None hier)
            assert start_time is not None
            _save_solution_results(solution, start_time)

            # Log Ergebnisse
            elapsed = time.time() - start_time
            add_log_message(LOG_SEPARATOR)
            add_log_message(f"✅ Solver beendet nach {elapsed:.2f}s")
            add_log_message(f"Status: {solution.solve_status}")
            add_log_message(f"Objective Value: {solution.objective_value:.2f}")

            # Aktualisiere UI
            solution_info.refresh()

        except Exception as e:
            _handle_solver_error(e, old_stdout)
        finally:
            _cleanup_solver_thread(old_stdout)

    def _save_instance_statistics(instance, method_config: dict[str, Any]) -> None:
        """Speichert Instance-Statistiken im State.

        Args:
            instance: Die zu lösende Instance
            method_config: Konfiguration der Solver-Methode
        """
        state.update_solver_statistics("num_employees", len(instance.employees))
        state.update_solver_statistics("num_days", instance.number_of_days)
        state.update_solver_statistics("num_shift_types", len(instance.shift_types))
        state.update_solver_statistics("method", method_config["name"])

    def _save_solution_results(solution, start_time: float) -> None:
        """Speichert Lösungs-Ergebnisse im State.

        Args:
            solution: Die gefundene Lösung
            start_time: Startzeit des Solvers
        """
        state.set_solution(solution)
        state.set_solver_end_time(time.time())

        elapsed = time.time() - start_time

        state.set_solver_status(str(solution.solve_status))
        state.set_last_objective_value(solution.objective_value)
        state.update_solver_statistics("solve_time", elapsed)
        state.update_solver_statistics("objective_value", solution.objective_value)
        state.update_solver_statistics("status", str(solution.solve_status))

    def _handle_solver_error(error: Exception, old_stdout) -> None:
        """Behandelt Solver-Fehler.

        Args:
            error: Die aufgetretene Exception
            old_stdout: Der ursprüngliche stdout-Stream
        """
        sys.stdout = old_stdout
        state.set_solver_end_time(time.time())
        state.set_solver_status("ERROR")
        state.update_solver_statistics("error", str(error))
        add_log_message(f"❌ Fehler: {str(error)}")

    def _cleanup_solver_thread(old_stdout) -> None:
        """Räumt nach Beendigung des Solver-Threads auf.

        Args:
            old_stdout: Der ursprüngliche stdout-Stream
        """
        nonlocal is_running

        sys.stdout = old_stdout
        if state.get_solver_end_time() is None:
            state.set_solver_end_time(time.time())
        is_running = False
        state.set_solver_running(False)
        control_buttons.refresh()

    def start_solver(method_config: dict[str, Any]) -> None:
        """Startet den Solver in einem neuen Thread.

        Args:
            method_config: Dictionary mit Methoden-Konfiguration
        """
        nonlocal solver_thread, is_running, start_time, log_buffer

        if state.is_solver_running():
            ui.notify("Solver läuft bereits!", type="warning")
            return

        if not state.get_instance():
            ui.notify("Keine Instance geladen!", type="warning")
            return

        # Reset State und lokale Variablen
        state.reset_solver_state()
        log_buffer = []
        start_time = time.time()
        is_running = True

        # Setze State-Variablen
        state.set_solver_running(True)
        state.set_solver_start_time(start_time)
        state.set_solver_status("RUNNING")

        # UI Updates
        control_buttons.refresh()
        runtime_display.refresh()

        # Starte Thread und Runtime-Updater
        solver_thread = threading.Thread(
            target=lambda: solve_in_thread(method_config),
            daemon=True,
        )
        solver_thread.start()

        # Starte Runtime-Updater
        asyncio.create_task(runtime_updater())

    def stop_solver() -> None:
        """Stoppt den Solver (nur UI-Update, Thread läuft weiter aus)."""
        nonlocal is_running
        if is_running:
            add_log_message("⚠️ Solver-Stop angefordert...")
            ui.notify("Solver wird gestoppt (kann einen Moment dauern)", type="info")

    # UI-Aufbau
    with ui.card().classes("w-full mb-4"):
        ui.label("Solver").classes("text-2xl font-bold mb-4")

        # Instance/Solution Info
        with ui.column().classes("w-full gap-2"):
            instance_info()
            solution_info()

        ui.separator()

        # Laufzeit-Anzeige
        with ui.row().classes("w-full items-center gap-4 mb-4"):
            runtime_display()

        # Solver-Steuerung
        control_buttons()

        ui.separator()

        # Log-Anzeige
        with ui.column().classes("w-full"):
            ui.label("Solver Log").classes("text-lg font-bold mb-2")
            log_display()
