import pandas as pd

from .. import solution


def parse_solution_to_table(solution: solution.Solution) -> pd.DataFrame:
    df = pd.DataFrame({"Test1": [1, 2, 3], "Test2": [4, 5, 6]})
    print(df)
    return df
