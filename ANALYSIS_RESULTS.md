# Analyse-Ergebnisse Solutions

## Schnelle Übersicht

| Instance | Tage | MA | Wunsch-Erfüllung | Schicht-Auslastung | Solver Status |
|----------|------|----|-----------------|--------------------|---------------|
| Instance1 | 14 | 8 | 80.8% | 91.5% | 4 (Optimal) |
| Instance10 | 28 | 40 | 90.8% | 93.5% | 2 (Feasible) |
| Instance11 | 28 | 50 | 93.8% | 98.6% | 2 (Feasible) |
| Instance12 | 28 | 60 | 78.7% | 95.6% | 2 (Feasible) |
| Instance13 | 28 | 120 | 72.9% | 98.2% | 2 (Feasible) |
| Instance14 | 42 | 32 | 85.8% | 103.6% | 2 (Feasible) |
| Instance15 | 42 | 45 | 66.1% | 101.0% | 2 (Feasible) |
| Instance16 | 56 | 20 | 82.1% | 104.3% | 2 (Feasible) |
| Instance17 | 56 | 32 | 84.6% | 102.6% | 2 (Feasible) |
| Instance18 | 84 | 22 | 80.9% | 101.4% | 2 (Feasible) |
| Instance19 | 84 | 40 | 81.5% | 101.5% | 2 (Feasible) |
| Instance1ExtraLong | 28 | 8 | 80.8% | 91.5% | 4 (Optimal) |
| Instance2 | 14 | 14 | 71.0% | 92.6% | 4 (Optimal) |
| Instance20 | 182 | 50 | 70.0% | 115.7% | 2 (Feasible) |
| Instance3 | 14 | 20 | 98.4% | 93.5% | 4 (Optimal) |
| Instance4 | 28 | 10 | 85.9% | 90.7% | 2 (Feasible) |
| Instance5 | 28 | 16 | 77.4% | 96.5% | 2 (Feasible) |
| Instance6 | 28 | 18 | 80.7% | 94.6% | 2 (Feasible) |
| Instance7 | 28 | 20 | 81.5% | 96.8% | 2 (Feasible) |
| Instance8 | 28 | 30 | 71.6% | 97.9% | 2 (Feasible) |
| Instance9 | 28 | 36 | 89.2% | 99.0% | 2 (Feasible) |

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

## Zusammenfassung

**Wunscherfüllung:**
- 🥇 Best: **Instance3** (98.4%)
- 🥉 Worst: **Instance15** (66.1%)
- Ø Durchschnitt: **81.2%**

**Schichtauslastung:**
- 🥇 Best: **Instance20** (115.7%)
- 🥉 Worst: **Instance4** (90.7%)
- Ø Durchschnitt: **98.1%**

**Solver-Status:**
- ✅ OPTIMAL (Status 4): 4 Instanzen
- ⏳ FEASIBLE (Status 2): 17 Instanzen

## Erkenntnisse

### Korrelation: Größe vs. Erfüllung

**Kleine Instanzen (≤20 MA)**: Meist bessere Wunscherfüllung
**Große Instanzen (>20 MA)**: Schlechtere Wunscherfüllung

**Tendenz**: Mit mehr Mitarbeitern ist es schwerer, individuelle Wünsche zu erfüllen.

### Solver-Performance

→ OPTIMAL-Lösungen sind meist **schneller und haben bessere Metriken** als FEASIBLE-Lösungen (Timeout)
