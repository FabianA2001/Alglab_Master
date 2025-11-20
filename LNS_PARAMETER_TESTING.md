# LNS Parameter Testing Framework

Dieses Framework ermöglicht es, systematisch verschiedene Parameter-Kombinationen für den Large Neighborhood Search (LNS) Algorithmus zu testen.


mit `lns-find` können die akutellen parameter getestet werden 

und mit `lns-show` die ergebnise angezeigt werden


## Ordnerstruktur

Nach dem Ausführen der Tests wird folgende Struktur erstellt:

```
lns_parameter_tests/
└── batch_20241119_143022/          # Ein Ordner pro parameter_grid
    ├── parameter_grid.json         # Das getestete Parameter-Grid
    ├── config_run_0.json          # Konfiguration für Run 0
    ├── run_0.log                  # Detaillierte Logs für Run 0
    ├── result_run_0.json          # Ergebnisse für Run 0
    ├── config_run_1.json          # Konfiguration für Run 1
    ├── run_1.log                  # Detaillierte Logs für Run 1
    ├── result_run_1.json          # Ergebnisse für Run 1
    └── ...
```

**Wichtig**: Alle Tests eines `parameter_grid` Aufrufs werden im selben Batch-Ordner gespeichert.


## Verwendung


### 3. Ergebnisse analysieren

```python
from pathlib import Path
from src.LNS.show_parameter import ResultAnalyzer

# Analyzer erstellen und Ergebnisse laden
analyzer = ResultAnalyzer(Path("lns_parameter_tests"))
analyzer.load_all_results()

# Summary anzeigen
analyzer.print_summary()

# Parameter vergleichen
analyzer.compare_parameter("start_search_window_size", "Instance1")

# Beste Parameter für eine Instanz finden
best_params = analyzer.get_best_parameters_by_instance("Instance1")
print(best_params)

# Nach CSV exportieren
analyzer.export_to_csv(Path("results.csv"))
```
