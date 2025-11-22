# Analyse-Ergebnisse Solutions

## Schnelle Übersicht

| Instance | Tage | MA | Wunsch-Erfüllung | Schicht-Auslastung | Solver Status |
|----------|------|----|-----------------|--------------------|---------------|
| Instance1 | 14 | 8 | **80.8%** | 91.5% | 4 (Optimal) |
| Instance13 | 28 | 120 | 68.0% | 97.1% | 2 (Feasible) |
| Instance1ExtraLong | 28 | 8 | 84.6% | 93.0% | 4 (Optimal) |
| Instance2 | 14 | 14 | 71.0% | 92.6% | 2 (Feasible) |
| Instance3 | 14 | 20 | **98.4%** | 93.5% | 4 (Optimal) |
| Instance4 | 28 | 10 | **90.1%** | 91.2% | 2 (Feasible) |
| Instance5 | 28 | 16 | 73.6% | 96.5% | 2 (Feasible) |
| Instance6 | 28 | 18 | 76.3% | 94.3% | 2 (Feasible) |
| Instance7 | 28 | 20 | 78.6% | 97.1% | 2 (Feasible) |
| Instance8 | 28 | 30 | 72.0% | 97.1% | 2 (Feasible) |
| Instance9 | 28 | 36 | **89.7%** | **99.0%** | 2 (Feasible) |

## Metriken erklärt

### Wunscherfüllung (`satisfaction_rate_percent`)
- **Definition**: Prozentsatz der erfüllten Wünsche (auf und ab Wünsche)
- **Berechnung**: `(erfüllte_wünsche / gesamt_wünsche) * 100`
- **Bereich**: 0-100%

### Schichtauslastung (`overall_utilization_percent`)
- **Definition**: Prozentsatz der Schichtauslastung im Vergleich zur gewünschten Besetzung
- **Berechnung**: `(zugeteilte_mitarbeiter / gewünschte_mitarbeiter) * 100`
- **Bereich**: 0-100%+ (kann über 100% sein, wenn Schicht überbesetzt)

### Unter-/Überbesetzung
- **`below_preferred`**: Wie viele Mitarbeiter unter der gewünschten Besetzung fehlen
- **`above_preferred`**: Wie viele Mitarbeiter über der gewünschten Besetzung hinzugekommen sind

## Wunscherfüllung

**Beste Erfüllung:**
- 🥇 **Instance3**: 98.4% (14 Tage, 20 MA)
- 🥈 **Instance9**: 89.7% (28 Tage, 36 MA)
- 🥉 **Instance4**: 90.1% (28 Tage, 10 MA)

**Schwächste Erfüllung:**
- Instance13: 68.0% (28 Tage, 120 MA) - sehr komplexe Instanz
- Instance2: 71.0% (14 Tage, 14 MA)
- Instance8: 72.0% (28 Tage, 30 MA)

**Durchschnitt: 80.4%**

## Schichtauslastung

**Beste Auslastung:**
- 🥇 **Instance9**: 99.0% (fast perfekt besetzt)
- 🥈 **Instance13**: 97.1%
- 🥈 **Instance7**: 97.1%

**Schwächste Auslastung:**
- Instance4: 91.2%
- Instance2: 92.6%
- Instance1ExtraLong: 93.0%

**Durchschnitt: 94.5%**

## Korrelation: Größe vs. Erfüllung

- **Kleine Instanzen (8-20 MA)**: Meist bessere Wunscherfüllung (71-98.4%)
- **Große Instanzen (30-120 MA)**: Schlechtere Wunscherfüllung (68-72%)
- **Mittlere Instanzen (16-20 MA)**: Gute Balance (78.6-89.7%)

**Tendenz**: Mit mehr Mitarbeitern ist es schwerer, individuelle Wünsche zu erfüllen.

## Solver-Status

- **Status 4 (OPTIMAL)**: 3 Instanzen (Instance1, Instance3, Instance1ExtraLong)
  - Solvetime: 0.07 - 0.12s
  
- **Status 2 (FEASIBLE)**: 8 Instanzen
  - Solvetime: 60.02 - 60.09s (bei Timeout!)

→ Die OPTIMAL-Lösungen sind meist **schneller und haben bessere Metriken**

## Detaillierte Problemschichten

### Instance6: Überbesetzung
- Tag 17: Schicht 1 ist zu 200% besetzt (4 statt 2 Mitarbeiter)
- Tag 17: Schicht 2 und 3 sind zu 150% besetzt

### Instance13: Kritische Unterbelegung
- Tag 5-6: Mehrere Schichten zu 20-25% besetzt
- Grund: 120 Mitarbeiter mit vielen Einschränkungen (komplexe Instanz)

### Instance8: Bestimmte Schichten unbesetzt
- Tag 5 und 9: Schicht 4 komplett unbesetzt (0/5, 0/3)
- Könnte Constraint-Verstoß sein oder nicht genug verfügbare Mitarbeiter
