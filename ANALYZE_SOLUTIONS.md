# Solution Analyser

Ein Script zur Analyse von fertigen Solutions und deren Qualitätsmetriken.

## Überblick

Das `analyze_solutions.py` Modul ermöglicht die detaillierte Analyse von Solutions bezüglich:

- **Wunscherfüllung**: Wie viel Prozent der Mitarbeiterwünsche (an bestimmten Tagen arbeiten/nicht arbeiten) wurden erfüllt?
- **Schichtauslastung**: Wie voll sind die Schichten prozentual im Vergleich zur gewünschten Besetzung?

## Nutzung

### Quick Start

Einfach das Script ausführen:

```bash
cd /Users/maccaroline/AlgLabMaster/Alglab_Master
python run_solution_analysis.py
```

### Im Python-Code

```python
from src.analyze_solutions import (
    analyze_all_solutions,
    analyze_solution_quality,
    print_analysis_summary,
    save_analysis_to_json,
)

# Alle Solutions analysieren
results = analyze_all_solutions()

# Ergebnisse anzeigen
print_analysis_summary(results)

# Als JSON speichern
save_analysis_to_json(results)
```

### Eine einzelne Solution analysieren

```python
from src.solution import Solution
from src.analyze_solutions import analyze_solution_quality

# Solution laden
solution = Solution.from_json_file("Instance1")

# Analysieren
analysis = analyze_solution_quality(solution)

# Ausgabe
print(f"Wunscherfüllung: {analysis['wishes']['satisfaction_rate_percent']:.1f}%")
print(f"Schichtauslastung: {analysis['shifts']['overall_utilization_percent']:.1f}%")
```

## Ausgabeformat

### Konsolen-Ausgabe

```
📊 Instance1
────────────────────────────────────────────────────────────────────────────────
  Instance: Instance1
  Größe: 14 Tage, 8 Mitarbeiter, 1 Schichttypen

  🎯 WÜNSCHE:
    Gesamt: 26 Wünsche
    Erfüllt: 21 Wünsche
    Quote: 80.8%

  📋 SCHICHTAUSLASTUNG:
    Gewünscht: 71 Mitarbeiter
    Zugeteilt: 65 Mitarbeiter
    Auslastung: 91.5%

  📉 Unterbelegte Schichten (Top 5):
    Tag 6, Schicht ...: 2/5 (40.0%)
    Tag 5, Schicht ...: 3/5 (60.0%)
    Tag 12, Schicht ...: 5/6 (83.3%)

  ⏱️ Solver Info:
    Objective Value: 607.0
    Solve Time: 0.07s
    Solve Status: 4
```

### JSON-Output (`data/analyses_summary.json`)

```json
{
  "Instance1": {
    "instance_name": "Instance1",
    "num_days": 14,
    "num_employees": 8,
    "num_shift_types": 1,
    "wishes": {
      "total_wishes": 26,
      "satisfied_wishes": 21,
      "satisfaction_rate_percent": 80.77,
      "satisfaction_rate": 0.8077
    },
    "shifts": {
      "total_preferred": 71,
      "total_assigned": 65,
      "overall_utilization_percent": 91.55,
      "overall_utilization": 0.9155,
      "details": [
        {
          "day": 0,
          "shift_type": 327176...,
          "preferred": 5,
          "assigned": 5,
          "utilization_percent": 100.0,
          "below_preferred": 0,
          "above_preferred": 0
        },
        ...
      ]
    },
    "objective_value": 607.0,
    "solve_time": 0.07,
    "solve_status": 4
  },
  ...
}
```

## Methoden

### `analyze_solution_quality(solution: Solution) -> dict`

Analysiert eine einzelne Solution.

**Parameter:**
- `solution`: Solution-Objekt

**Rückgabe:**
```python
{
    'instance_name': str,
    'num_days': int,
    'num_employees': int,
    'num_shift_types': int,
    'wishes': {
        'total_wishes': int,
        'satisfied_wishes': int,
        'satisfaction_rate_percent': float,  # 0-100
        'satisfaction_rate': float,           # 0-1
    },
    'shifts': {
        'total_preferred': int,
        'total_assigned': int,
        'overall_utilization_percent': float,  # 0-100+
        'overall_utilization': float,          # 0-1+
        'details': [
            {
                'day': int,
                'shift_type': int,
                'preferred': int,
                'assigned': int,
                'utilization_percent': float,
                'below_preferred': int,
                'above_preferred': int
            },
            ...
        ]
    },
    'objective_value': float,
    'solve_time': float,
    'solve_status': int,
}
```

### `analyze_all_solutions(solutions_dir: Optional[Path]) -> dict`

Analysiert alle Solutions aus einem Verzeichnis (default: `data/solutions`).

**Parameter:**
- `solutions_dir` (optional): Pfad zum Solutions-Verzeichnis

**Rückgabe:**
```python
{
    'solution_name_1': {...},  # Result von analyze_solution_quality
    'solution_name_2': {...},
    ...
}
```

### `print_analysis_summary(analysis_results: dict) -> None`

Gibt eine formatierte Zusammenfassung aller Analysen auf der Konsole aus.

### `save_analysis_to_json(analysis_results: dict, output_path: Optional[Path]) -> None`

Speichert die Analyse-Ergebnisse als JSON-Datei.

**Parameter:**
- `analysis_results`: Dict von Analyse-Ergebnissen
- `output_path` (optional): Output-Pfad (default: `data/analyses_summary.json`)

## Metriken erklärt

### Wunscherfüllung (`satisfaction_rate_percent`)

- **Definition**: Prozentsatz der erfüllten Wünsche (auf und ab Wünsche)
- **Berechnung**: `(erfüllte_wünsche / gesamt_wünsche) * 100`
- **Bereich**: 0-100%
- **Beispiel**: 80.8% bedeutet dass von 26 Wünschen 21 erfüllt wurden

### Schichtauslastung (`overall_utilization_percent`)

- **Definition**: Prozentsatz der Schichtauslastung im Vergleich zur gewünschten Besetzung
- **Berechnung**: `(zugeteilte_mitarbeiter / gewünschte_mitarbeiter) * 100`
- **Bereich**: 0-100%+ (kann über 100% sein, wenn Schicht überbesetzt)
- **Beispiel**: 91.5% bedeutet dass Schichten im Durchschnitt zu 91.5% besetzt sind

### Unter-/Überbesetzung

- **`below_preferred`**: Wie viele Mitarbeiter unter der gewünschten Besetzung fehlen
- **`above_preferred`**: Wie viele Mitarbeiter über der gewünschten Besetzung hinzugekommen sind

## Integration mit Callback_Solver

Das Analyse-Modul nutzt die gleiche Logik wie der `callback_solver.py`:

```python
# callback_solver.py macht:
pref = shift.preffert_number_employees
below = self.Value(self.vars.below_prefferd_vars[(day, type_uid)])

# analyze_solutions.py macht:
preferred = shift.preffert_number_employees
assigned = sum(1 for (d, t, e), v in vars_map.items() if d == day and t == type_uid and v == 1)
utilization_percent = (assigned / preferred) * 100
```

Dadurch sind die Metriken konsistent zwischen Löser und Analyse!

## Beispiel-Output

```
🔍 Analysiere alle Solutions...

Finde 11 Solution-Dateien in /Users/maccaroline/AlgLabMaster/Alglab_Master/data/solutions

✓ Analysiert: Instance1
✓ Analysiert: Instance13
✓ Analysiert: Instance1ExtraLong
...

================================================================================
ANALYSE DER SOLUTIONS
================================================================================

────────────────────────────────────────────────────────────────────────────────
📊 Instance1
────────────────────────────────────────────────────────────────────────────────
  Instance: Instance1
  Größe: 14 Tage, 8 Mitarbeiter, 1 Schichttypen

  🎯 WÜNSCHE:
    Gesamt: 26 Wünsche
    Erfüllt: 21 Wünsche
    Quote: 80.8%

  📋 SCHICHTAUSLASTUNG:
    Gewünscht: 71 Mitarbeiter
    Zugeteilt: 65 Mitarbeiter
    Auslastung: 91.5%

  📉 Unterbelegte Schichten (Top 5):
    Tag 6, Schicht 327176509795513342126021012545780561845: 2/5 (40.0%)
    Tag 5, Schicht 327176509795513342126021012545780561845: 3/5 (60.0%)
    Tag 12, Schicht 327176509795513342126021012545780561845: 5/6 (83.3%)

  ⏱️ Solver Info:
    Objective Value: 607.0
    Solve Time: 0.07s
    Solve Status: 4

✓ Analysen gespeichert in: /Users/maccaroline/AlgLabMaster/Alglab_Master/data/analyses_summary.json
```
