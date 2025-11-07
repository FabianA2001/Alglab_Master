## Instance Modifier or "Result from Solver" Modifier

**1. Modification Options:**
- Should we modify the instance directly or allow users to specify their wanted changes in the displayed solution?

**2. User Change the displayed solution:**
If a user wants to specify their wanted changes in the displayed solution, the following approaches are possible:

**2.1. Solution Change:**
- For instance, if an employee shouldn’t work on a specific day, we may:
  - 2.1.1. Minimize changes (see attached photo).
  - 2.1.2. Introduce constraints to limit the number of changes, ensuring they resemble the objective function but with integer inequalities(see attached photo).
- If we want to keep a high original function value:
  - 2.1.3. Add a constraint to keep the value of the original objective function "high".

**2.2. Solution Change + :**
- Users might choose which days to alter (in order to achieve their goal change).
- 2.2.1. Adding constraints based on chosen days (not chosen) can achieve this(see attached photo).
- 2.2.2. Considering weeks instead of days could be advantageous, as it might increase the likelihood of finding a solution. If no feasible solution can be found, we should account for it nonetheless.

---

## 3. Coverage Constraint:
- You mentioned that disabling a constraint (e.g., coverage) does not affect the solution. 

**3.1. Questions:**
- In `instance1.txt`, shouldn't the weight for "Weight for over" be negative? Because it should minimize our objective function.

---

## 4. Git Structure

**4.1. Current Process:**
- Each person has their own branch (feature_branch).
- When a feature is complete, a pull request is submitted.
- Merge conflicts are resolved by the developer who made the changes.
- Other team members review the pull request, providing comments or simply approving it.

**4.2. Questions:**
- Should we implement a better structure in our Git workflow?
- Do we want to use CI checks for our main branch?

**4.3. Additional Information:**
- The other team has created an analysis interface. Should we begin working on that now, or hold off for the moment?