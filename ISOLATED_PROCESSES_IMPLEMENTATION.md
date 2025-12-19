# Implementation: Isolated Processes für warm_start_half_instance

## Zusammenfassung

Die `warm_start_half_instance` Methode in der `Solver` Klasse wurde modifiziert, um jede der 4 Quarter-Instanzen in einem separaten Python-Prozess zu lösen. Dies verhindert das Performance-Degradation-Problem von CP-SAT, das bei häufigem Lösen hintereinander auftritt.

## Änderungen

### 1. **src/solver.py**
   - Modified `warm_start_half_instance()` method
   - Jeder Quarter wird jetzt mit `subprocess.run()` in einem neuen Python-Prozess gelöst
   - Serialisierung der Instance und Solution über `pickle` (binär)
   - Temporäre Dateien für Instance und Solution
   - Fehlerbehandlung und Timeouts für jeden Subprocess

### 2. **src/solver_worker.py** (NEU)
   - Neues Worker-Modul für isolierte Prozesse
   - Wird mit `python -m src.solver_worker --instance <pkl> --output <pkl> --timeout <seconds>` aufgerufen
   - Lädt die Instance aus pickle, löst sie mit einem neuen Solver und speichert die Solution

### 3. **test_warm_start_half_instance.py** (NEU)
   - Einfaches Test-Skript zum Validieren der neuen Funktionalität
   - Lädt Instance10, löst sie mit `warm_start_half_instance` und zeigt Ergebnisse

## Wie es funktioniert

1. `warm_start_half_instance` erstellt 4 Quarter-Instanzen (je 1/4 der Mitarbeiter)
2. Für jeden Quarter:
   - Instance wird zu Pickle-Datei serialisiert
   - Neuer Python-Prozess wird gestartet: `python -m src.solver_worker --instance ... --output ... --timeout ...`
   - Solution wird aus Pickle-Datei deserialisiert
   - Hints werden zur Hauptinstanz hinzugefügt
3. Die Hauptinstanz wird mit allen Hints gelöst

## Vorteile

- ✅ Verhindert CP-SAT Performance-Degradation bei wiederholtem Lösen
- ✅ Jeder Quarter läuft in einem sauberen Python-Prozess
- ✅ Fehlerbehandlung mit Timeouts pro Quarter
- ✅ Ähnlich wie `--isolate` Option in run_benchmark.py
- ✅ Transparent für Benutzer - gleiche API wie vorher

## Testing

```bash
python test_warm_start_half_instance.py
```

Oder mit dem Benchmark-Skript:

```bash
python -m benchmarks.run_benchmark --start-instance 20 --limit 1 --timeout 600 --output benchmarks/results -n Halfinstance_{timestamp}.json
```
