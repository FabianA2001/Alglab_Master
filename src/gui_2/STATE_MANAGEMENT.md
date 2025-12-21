# State-Management in der GUI

## Übersicht

Das State-Management ermöglicht es, Daten zwischen verschiedenen Seiten der Anwendung zu teilen.
Der State wird in `app.storage.general` gespeichert und ist während der gesamten Laufzeit verfügbar.

## Verwendung

### 1. State in einer Seite nutzen

```python
from .. import state

def my_page():
    # Lese aktuelle Instance
    current_instance = state.get_instance()
    
    # Lese aktuelle Solution
    current_solution = state.get_solution()
    
    # Setze neue Solution (wird auf allen Seiten verfügbar)
    state.set_solution(new_solution)
    
    # Setze neue Instance
    state.set_instance(new_instance)
```

### 2. Beispiel: Instance auf Instance-Seite laden

**instance_page.py:**
```python
from .. import state

def instance_page():
    def load_instance(instance_name: str):
        instance_path = DATA_DIR / instance_name
        loaded_instance = parseTXT.parse_txt(instance_path)
        
        # Setze im globalen State - verfügbar auf allen anderen Seiten!
        state.set_instance(loaded_instance)
        
        ui.notify("Instance geladen!")
```

### 3. Beispiel: Instance auf Solver-Seite verwenden

**solver_page.py:**
```python
from .. import state

def solver_page():
    def update_instance_info():
        # Hole aktuelle Instance aus globalem State
        current_instance = state.get_instance()
        
        if current_instance:
            ui.label(f"Instance geladen: {len(current_instance.employees)} Mitarbeiter")
        else:
            ui.label("Keine Instance geladen")
    
    # Initial anzeigen
    update_instance_info()
    
    # Button zum manuellen Aktualisieren
    ui.button("Aktualisieren", on_click=update_instance_info)
```

### 4. Beispiel: Solution erstellen und speichern

**solver_page.py:**
```python
from .. import state

def solver_page():
    def solve():
        # Hole Instance aus State
        instance = state.get_instance()
        
        if not instance:
            ui.notify("Keine Instance geladen!", type="warning")
            return
        
        # Erstelle Solution
        solution = run_solver(instance)
        
        # Speichere im State - verfügbar auf Solution-Seite!
        state.set_solution(solution)
        
        ui.notify("Solution erstellt!")
```

## Verfügbare Funktionen

### Instance-Verwaltung
- `state.set_instance(instance)`: Setzt die aktuelle Instance
- `state.get_instance()`: Gibt die aktuelle Instance zurück (oder None)

### Solution-Verwaltung
- `state.set_solution(solution)`: Setzt die aktuelle Solution
- `state.get_solution()`: Gibt die aktuelle Solution zurück (oder None)

### Solver-Status
- `state.set_solver_running(True/False)`: Setzt den Solver-Status
- `state.is_solver_running()`: Prüft ob Solver läuft

## Wichtig

- Der State wird im `app.storage.general` gespeichert
- State ist **während der Laufzeit persistent**
- Bei einem Neustart der Anwendung geht der State verloren
- **Kein automatisches Update**: Seiten müssen manuell aktualisiert werden (z.B. durch Button oder beim Seitenwechsel)
- Jede Seite liest beim Laden automatisch den aktuellen State

## Best Practices

1. **Immer prüfen ob Daten vorhanden sind:**
   ```python
   instance = state.get_instance()
   if instance is None:
       ui.notify("Bitte zuerst Instance laden")
       return
   ```

2. **Update-Buttons für manuelle Aktualisierung bereitstellen:**
   ```python
   ui.button("State aktualisieren", on_click=update_display)
   ```

3. **State beim Laden der Seite initialisieren:**
   ```python
   def my_page():
       # ... UI aufbauen ...
       
       # Initial anzeigen falls vorhanden
       if state.get_instance() is not None:
           update_display()
   ```
