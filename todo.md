
### generelle Ziele

- website (taipy oder streamlit) (Fabian)
- - upper / lower bound
- - objektiv value
- - Instanze laden/ bearbeiten / erstellen
- - Ergenisee "schön" darstellen

- input/output test (Solver-Agnostic Validation)
- 

### nächste Ziele
- instance parser (Fabian)
- Solver klasse (Full Solver) (Mohammed)
- - Solution callback
- - parameter für solver
- Solution klasse (Mohammed)

```class NurseRosteringSolution(BaseModel):
    """
    This schema defines the OUTPUT for the nurse rostering problem.
    """
    nurses_at_shifts: dict[ShiftUid, list[NurseUid]] = Field(
        ..., description="Maps shift UIDs to lists of assigned nurse UIDs."
    )
    objective_value: int = Field(
        description="Objective value of the computed solution."
    )
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Time when the solution was generated. Takes little space and can be extremely useful when investigating issues with the solution. Optimally, also add the revision of the algorithm that generated the solution, e.g., by using a git commit hash.",
    )
    # Validation of the solution will be handled in a separate module.
```
- Objectiv (Caro)


https://d-krupke.github.io/cpsat-primer/test_driven_optimization.html#full-solver