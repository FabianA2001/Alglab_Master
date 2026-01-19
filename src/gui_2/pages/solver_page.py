"""Solver-Seite für die GUI.

Bietet eine Benutzeroberfläche zur Konfiguration und Ausführung
verschiedener Solver-Methoden mit Echtzeit-Logging und Laufzeitanzeige.
"""

import asyncio
import os
import sys
import threading
import time
import traceback
from datetime import datetime
from typing import Any

from nicegui import ui

from ...LNS import lns, minimal_change_lns
from ...solve_employees import solve_employee
from ...shift_vars import Shift_vars
from ...solver import Solver
from ...callback_early_stop import Callback_Early_Stop
from .. import state

# Konstanten
LOG_SEPARATOR = "─" * 60
MAX_LOG_STORAGE = 1000  # Maximale Anzahl gespeicherter Log-Zeilen
MAX_LOG_DISPLAY = 50  # Anzahl angezeigter Zeilen (Rest ist scrollbar)
DEFAULT_TIMEOUT_SECONDS = 300.0
RUNTIME_UPDATE_INTERVAL = 0.1


def solver_page() -> None:
    """Seite für Solver-Konfiguration und -Ausführung."""

    # Lokale State-Variablen
    solver_thread: threading.Thread | None = None
    log_buffer: list[str] = []
    start_time: float | None = None
    is_running: bool = False

    # Log-HTML Element und Scroll Area (werden später initialisiert)
    log_html_element = None
    log_scroll_area = None

    # Konfiguration der verfügbaren Solver-Methoden
    solver_methods = [
        {
            "name": "Standard Solve",
            "description": "Standard CP-SAT Solver",
            "icon": "play_arrow",
            "method": "solve",
            "color": "positive",
            "params": {
                "log_search_progress": True,
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
                "log_search_progress": True,
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
                "log_search_progress": True,
                "max_time_in_seconds": 60.0,
                "stop_after_first_solution": True,
            },
        },
        {
            "name": "Large Neighborhood Search",
            "description": "LNS-Solver für große Nachbarschaftssuche",
            "icon": "explore",
            "method": "lns",
            "color": "info",
            "params": {
                "timeout_seconds": DEFAULT_TIMEOUT_SECONDS,
            },
            "requires_solution": True,
        },
        {
            "name": "Minimal Changes LNS",
            "description": "LNS mit minimalen Änderungen an bestehender Lösung",
            "icon": "build",
            "method": "minimal_change_lns",
            "color": "warning",
            "params": {
                "max_solve_time": DEFAULT_TIMEOUT_SECONDS,
                "log_search_progress": True,
            },
            "requires_solution": True,
        },
        {
            "name": "Minimal Changes Warm Start",
            "description": "Minimal Changes with hints from previous solution",
            "icon": "build",
            "method": "warm_start",
            "color": "warning",
            "params": {
                "max_time_in_seconds": DEFAULT_TIMEOUT_SECONDS,
            },
            "requires_solution": True,
        },
        {
            "name": "Only Warm Start",
            "description": "Resume normal optimization with hints from previous solution",
            "icon": "build",
            "method": "normal_warm_start",
            "color": "warning",
            "params": {
                "max_time_in_seconds": DEFAULT_TIMEOUT_SECONDS,
            },
            "requires_solution": True,
        },
        {
            "name": "First Solution",
            "description": "Use one shift method to find a first solution quickly",
            "icon": "build",
            "method": "solve_instance_one_shift",
            "color": "warning",
            "params": {
                "one_shift_max_time": 0 * 60,
                "fixed_work_var_opt_max_time": 0 * 60,
                "general_optimization_max_time": 0 * 60,
            },
            "requires_solution": False,
        },
        {
            "name": "First OK Solution",
            "description": "Use one shift method to find an OK solution quickly",
            "icon": "build",
            "method": "solve_instance_one_shift",
            "color": "warning",
            "params": {
                "one_shift_max_time": 10 * 60,
                "fixed_work_var_opt_max_time": 10 * 60,
                "general_optimization_max_time": 0 * 60,
            },
            "requires_solution": False,
        },
        {
            "name": "First good Solution",
            "description": "Use one shift method to find an OK solution quickly",
            "icon": "build",
            "method": "solve_instance_one_shift",
            "color": "warning",
            "params": {
                "one_shift_max_time": 10 * 60,
                "fixed_work_var_opt_max_time": 10 * 60,
                "general_optimization_max_time": DEFAULT_TIMEOUT_SECONDS,
            },
            "requires_solution": False,
        },
        # TODO add first solution fast, and ok and warm_start without minimal changes,
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
    def timeout_config() -> None:
        """Zeigt die Timeout-Konfiguration an."""
        current_timeout = state.get_solver_timeout()
        assert current_timeout is not None

        with ui.row().classes("items-center gap-4"):
            ui.label("Timeout:").classes("font-semibold")
            timeout_input = ui.number(
                label="Sekunden",
                value=current_timeout,
                min=1,
                max=3600,
                step=10,
                format="%.0f",
                on_change=lambda e: state.set_solver_timeout(
                    e.value if e.value else DEFAULT_TIMEOUT_SECONDS
                ),
            ).classes("w-32")
            ui.label(f"({current_timeout / 60:.1f} Minuten)").classes(
                "text-sm text-gray-600"
            )

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
        """Zeigt die Solver-Logs an (bis zu 1000 Zeilen, scrollbar verfügbar)."""
        nonlocal log_html_element, log_scroll_area

        with ui.scroll_area().classes(
            "w-full h-96 bg-gray-100 p-4 font-mono text-sm"
        ) as scroll:
            log_html_element = ui.html("", sanitize=False)
            log_scroll_area = scroll
            # Speichere im State für Background-Updates
            state.solver_log_html_element = log_html_element
            state.solver_log_scroll_area = log_scroll_area
            update_log_content()

    def update_log_content() -> None:
        """Aktualisiert nur den Log-Inhalt ohne die gesamte Komponente neu zu laden."""
        # Versuche zuerst lokale Referenz, dann State-Referenz
        html_element = (
            log_html_element
            if log_html_element is not None
            else getattr(state, "solver_log_html_element", None)
        )
        scroll_element = (
            log_scroll_area
            if log_scroll_area is not None
            else getattr(state, "solver_log_scroll_area", None)
        )

        if html_element is not None:
            logs = state.get_solver_logs()
            recent_logs = logs[-MAX_LOG_STORAGE:]
            try:
                html_element.content = "<pre>" + "\n".join(recent_logs) + "</pre>"
                # Auto-Scroll nach unten (nur wenn scroll_area noch gültig ist)
                if scroll_element is not None:
                    scroll_element.scroll_to(percent=1.1)
            except (RuntimeError, AttributeError):
                # Element wurde gelöscht oder ist nicht mehr gültig
                pass

    @ui.refreshable
    def control_buttons() -> None:
        """Zeigt die Steuerungs-Buttons an."""
        can_start = state.get_instance() is not None and not state.is_solver_running()
        is_solver_active = state.is_solver_running()
        has_solution = state.get_solution() is not None

        with ui.column().classes("w-full gap-4"):
            # Solver-Methoden Buttons
            ui.label("Solver-Methoden").classes("text-lg font-bold")
            with ui.grid(columns=3).classes("w-full gap-2"):
                for method_config in solver_methods:
                    # Prüfe ob Methode eine Lösung benötigt
                    requires_solution = method_config.get("requires_solution", False)
                    can_use = can_start and (not requires_solution or has_solution)

                    button = ui.button(
                        method_config["name"],
                        icon=method_config["icon"],
                        on_click=lambda e, m=method_config: start_solver(m),
                    )
                    if can_use:
                        button.props(f"color={method_config['color']}")
                    button.set_enabled(can_use)

                    # Tooltip mit zusätzlicher Info für solution-abhängige Methoden
                    tooltip_text = method_config["description"]
                    if requires_solution and not has_solution:
                        tooltip_text += " (Benötigt existierende Lösung)"
                    button.tooltip(tooltip_text)

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
        # Refresh wird durch runtime_updater gesteuert

    async def runtime_updater() -> None:
        """Aktualisiert die Laufzeitanzeige kontinuierlich."""
        while state.is_solver_running():
            try:
                runtime_display.refresh()
                update_log_content()  # Aktualisiere nur den Log-Inhalt, nicht die ganze Komponente
            except (RuntimeError, AttributeError):
                # UI-Elemente nicht mehr verfügbar (Seitenwechsel)
                pass
            await asyncio.sleep(RUNTIME_UPDATE_INTERVAL)

    class TeeOutput:
        """Schreibt Output gleichzeitig in stdout und Log.

        Ermöglicht das Erfassen von Solver-Logs ohne
        die normale Konsolenausgabe zu unterdrücken.
        """

        def __init__(self, original_stdout) -> None:
            """Initialisiert den TeeOutput.

            Args:
                original_stdout: Der ursprüngliche stdout-Stream
            """
            self.original_stdout = original_stdout
            self.captured = []

        def write(self, text: str) -> int:
            """Schreibt Text in beide Streams.

            Args:
                text: Der zu schreibende Text
            """
            self.original_stdout.write(text)
            self.original_stdout.flush()
            if text.strip():
                # Speichere jede Zeile einzeln
                lines = text.rstrip().split("\n")
                for line in lines:
                    if line.strip():
                        self.captured.append(line)
                        add_log_message(line)
            return len(text)

        def flush(self) -> None:
            """Flusht beide Streams."""
            self.original_stdout.flush()

        def fileno(self):
            """Gibt File-Descriptor zurück."""
            return self.original_stdout.fileno()

    def solve_in_thread(method_config: dict[str, Any]) -> None:
        """Führt den Solver in einem separaten Thread aus.

        Args:
            method_config: Dictionary mit Methoden-Konfiguration
                - name: Anzeigename der Methode
                - method: Name der Solver-Methode
                - params: Parameter für die Solver-Methode
        """
        nonlocal is_running, start_time

        # Sichere Original stdout/stderr
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        old_stdout_fd = os.dup(1)
        old_stderr_fd = os.dup(2)

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

            add_log_message("⚙️ Solver initialisiert")
            add_log_message(f"🔍 Suche nach Lösung mit: {method_config['method']}...")
            add_log_message(LOG_SEPARATOR)

            # Erstelle Pipes für stdout/stderr Umleitung
            read_pipe, write_pipe = os.pipe()

            # Leite stdout und stderr auf OS-Ebene um
            os.dup2(write_pipe, 1)
            os.dup2(write_pipe, 2)

            # Erstelle neuen Python stdout/stderr
            sys.stdout = TeeOutput(os.fdopen(old_stdout_fd, "w"))
            sys.stderr = sys.stdout

            # Starte Thread zum Lesen der Pipe
            def read_output():
                with os.fdopen(read_pipe, "r") as pipe_reader:
                    for line in pipe_reader:
                        if line.strip():
                            add_log_message(line.rstrip())

            reader_thread = threading.Thread(target=read_output, daemon=True)
            reader_thread.start()

            # Führe Solver-Methode aus
            method_name = method_config["method"]

            # Hole aktuelles Timeout aus State und überschreibe Parameter
            current_timeout = state.get_solver_timeout()
            params = method_config["params"].copy()

            # Setze timeout je nach Methode mit richtigem Parameter-Namen
            if "max_time_in_seconds" in params:
                params["max_time_in_seconds"] = current_timeout
            elif "timeout_seconds" in params:
                params["timeout_seconds"] = current_timeout
            elif "max_solve_time" in params:
                params["max_solve_time"] = current_timeout
            elif (
                "general_optimization_max_time" in params
                and current_timeout is not None
            ):
                params["general_optimization_max_time"] = current_timeout
                params["general_optimization_max_time"] = (
                    current_timeout if current_timeout > 1 else 0
                )

            if method_name == "lns":
                # LNS-Solver
                inst_sol = state.get_solution()
                if inst_sol is None:
                    inst_sol = instance
                lns_solver = lns.LNS(inst_sol, **params)
                solution = lns_solver.solve()
            elif method_name == "minimal_change_lns":
                # Minimal Changes LNS - benötigt existierende Lösung
                old_solution = state.get_solution()
                if not old_solution:
                    raise ValueError(
                        "Minimal Changes LNS benötigt eine existierende Lösung!"
                    )
                # Verwende changed_days aus State, falls vorhanden
                days_with_change = state.get_changed_days()
                if len(days_with_change) == 0:
                    # Fallback: alle Tage verwenden
                    days_with_change = set(range(instance.number_of_days))
                    add_log_message(
                        "⚠️ Keine geänderten Tage angegeben - verwende alle Tage"
                    )
                else:
                    add_log_message(
                        f"ℹ️ Verwende {len(days_with_change)} geänderte Tage: {sorted(days_with_change)}"
                    )
                lokal_solution = old_solution.model_copy(deep=True)
                lokal_solution.instance = instance.model_copy(deep=True)
                solution = minimal_change_lns.solve_changes(
                    old_solution=lokal_solution,
                    days_with_change=list(days_with_change),
                    **params,
                )
            elif method_name == "solve_instance_one_shift":
                optimization_callback = Callback_Early_Stop(
                    instance, Shift_vars(instance)
                )
                # Note right now optimization time is the max_time_in_seconds, the rest is not limited but finish for each isntance relativily fast to the size of an instance
                solution = solve_employee(instance=instance).solve_instance_one_shift(
                    optimization_callback=optimization_callback,
                    **params,
                )
            elif method_name == "normal_warm_start":
                old_solution = state.get_solution()
                if not old_solution:
                    raise ValueError(
                        "Minimal Changes LNS benötigt eine existierende Lösung!"
                    )
                solution = Solver(instance, Shift_vars(instance)).warm_start_generalized(hint_solution=old_solution, **params)
            else:
                # Standard Solver-Methoden
                vars = Shift_vars(instance)
                solver = Solver(instance, vars)
                solver_method = getattr(solver, method_name)
                if method_config.get("requires_solution", False):
                    solution = solver_method(solution=state.get_solution(), **params)
                else:
                    solution = solver_method(**params)

            # Schließe Write-Ende der Pipe
            os.close(write_pipe)

            # Warte kurz auf Reader-Thread
            reader_thread.join(timeout=1.0)

            # Stelle stdout/stderr wieder her
            os.dup2(old_stdout_fd, 1)
            os.dup2(old_stderr_fd, 2)
            sys.stdout = old_stdout
            sys.stderr = old_stderr

            # Speichere Ergebnisse (start_time ist garantiert nicht None hier)
            assert start_time is not None
            _save_solution_results(solution, start_time)

            # Log Ergebnisse
            elapsed = time.time() - start_time
            add_log_message(LOG_SEPARATOR)
            add_log_message(f"✅ Solver beendet nach {elapsed:.2f}s")
            add_log_message(f"Status: {solution.solve_status}")
            add_log_message(f"Objective Value: {solution.objective_value:.2f}")

            # Aktualisiere UI - finale Refresh für Logs und Solution
            update_log_content()
            solution_info.refresh()

        except Exception as e:
            # Stelle stdout/stderr wieder her
            try:
                os.dup2(old_stdout_fd, 1)
                os.dup2(old_stderr_fd, 2)
                sys.stdout = old_stdout
                sys.stderr = old_stderr
            except:
                pass
            _handle_solver_error(e, old_stdout)
        finally:
            # Cleanup
            try:
                os.close(old_stdout_fd)
                os.close(old_stderr_fd)
            except:
                pass
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
        state.add_solution(solution)
        solution.to_json_file(solution.instance.name)
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

        # Formatiere Fehler mit Traceback-Informationen
        tb_lines = traceback.format_exception(type(error), error, error.__traceback__)
        tb_str = "".join(tb_lines)

        add_log_message(f"❌ Fehler: {type(error).__name__}: {str(error)}")
        add_log_message("Traceback:")
        for line in tb_str.split("\n"):
            if line.strip():
                add_log_message(line)

        update_log_content()

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

        # Starte Runtime-Updater (nur wenn noch keiner läuft)
        if (
            not hasattr(state, "solver_runtime_task")
            or state.solver_runtime_task is None
            or state.solver_runtime_task.done()
        ):
            state.solver_runtime_task = asyncio.create_task(runtime_updater())

    async def stop_solver() -> None:
        """Stoppt den Solver mit Bestätigung und beendet den Thread sauber."""
        nonlocal is_running, solver_thread

        if not is_running and not state.is_solver_running():
            ui.notify("Kein Solver läuft gerade", type="info")
            return

        with ui.dialog() as dialog, ui.card():
            ui.label("Solver wirklich stoppen?").classes("text-lg font-bold mb-4")
            ui.label(
                "Der Solver-Thread wird beendet. Dies kann zu unvollständigen Ergebnissen führen."
            ).classes("mb-4")
            ui.label(
                "⚠️ Warnung: Der aktuelle Lösungsfortschritt geht verloren!"
            ).classes("text-orange-600 mb-4")

            with ui.row().classes("w-full justify-end gap-2"):
                ui.button("Abbrechen", on_click=dialog.close).props("flat")
                ui.button(
                    "Ja, stoppen",
                    on_click=lambda: dialog.submit(True),
                ).props("color=negative")

        result = await dialog

        if not result:
            return

        # Bestätigt - Solver stoppen
        add_log_message("⚠️ Solver-Stop durch Benutzer angefordert...")
        add_log_message("🛑 Beende Solver-Thread...")

        # Setze Flags
        is_running = False
        state.set_solver_running(False)
        state.set_solver_end_time(time.time())
        state.set_solver_status("STOPPED_BY_USER")

        # Stoppe Runtime-Updater
        if (
            hasattr(state, "solver_runtime_task")
            and state.solver_runtime_task is not None
        ):
            try:
                state.solver_runtime_task.cancel()
                state.solver_runtime_task = None
            except:
                pass

        # Versuche Thread zu beenden (Python Threads können nicht direkt gekillt werden)
        # Der Thread wird beim nächsten Python-Statement oder IO-Operation beendet
        if solver_thread is not None and solver_thread.is_alive():
            add_log_message(
                "⏳ Warte auf Thread-Beendigung (kann einen Moment dauern)..."
            )
            # Hinweis: Python Threads können nicht zwangsweise beendet werden
            # Sie müssen auf natürliche Weise enden (z.B. wenn der Solver zurückkehrt)
            add_log_message("ℹ️ Hinweis: Der Solver-Prozess läuft noch zu Ende")

        add_log_message(LOG_SEPARATOR)
        add_log_message("🛑 Solver wurde gestoppt")

        # Update UI
        update_log_content()
        control_buttons.refresh()
        runtime_display.refresh()

        ui.notify("Solver wurde gestoppt", type="warning")

    # Initialisierung: Setze Default-Timeout falls noch nicht gesetzt
    if state.get_solver_timeout() == None:  # Default-Wert aus state.py
        state.set_solver_timeout(DEFAULT_TIMEOUT_SECONDS)

    # UI-Aufbau
    with ui.card().classes("w-full mb-4"):
        ui.label("Solver").classes("text-2xl font-bold mb-4")

        # Instance/Solution Info
        with ui.column().classes("w-full gap-2"):
            instance_info()
            solution_info()

        ui.separator()

        # Timeout-Konfiguration
        timeout_config()

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

    # Initialisierung: Wenn Solver bereits läuft, starte Updater
    # (muss nach UI-Aufbau sein, da runtime_display.refresh() aufgerufen wird)
    if state.is_solver_running():
        # Stoppe alte Runtime-Tasks
        if (
            hasattr(state, "solver_runtime_task")
            and state.solver_runtime_task is not None
        ):
            try:
                state.solver_runtime_task.cancel()
            except:
                pass
        # Starte neuen Runtime-Updater
        state.solver_runtime_task = asyncio.create_task(runtime_updater())
