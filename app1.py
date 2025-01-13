from pulp import COIN_CMD, LpStatus

def optimize_lineup(players, salary_cap, roster_size):
    problem = LpProblem("DraftKings_Lineup", LpMaximize)

    # Binary decision variables for each player
    player_vars = {row["name"]: LpVariable(row["name"], 0, 1, cat="Binary") for _, row in players.iterrows()}

    # Objective: Maximize projected points
    problem += lpSum(row["projection"] * player_vars[row["name"]] for _, row in players.iterrows())

    # Constraints
    problem += lpSum(row["salary"] * player_vars[row["name"]] for _, row in players.iterrows()) <= salary_cap
    problem += lpSum(player_vars[row["name"]] for _, row in players.iterrows()) == roster_size

    # Positional constraints
    problem += lpSum(player_vars[row["name"]] for _, row in players.iterrows() if "PG" in row["positions"]) >= 1
    problem += lpSum(player_vars[row["name"]] for _, row in players.iterrows() if "SG" in row["positions"]) >= 1
    problem += lpSum(player_vars[row["name"]] for _, row in players.iterrows() if "SF" in row["positions"]) >= 1
    problem += lpSum(player_vars[row["name"]] for _, row in players.iterrows() if "PF" in row["positions"]) >= 1
    problem += lpSum(player_vars[row["name"]] for _, row in players.iterrows() if "C" in row["positions"]) >= 1

    # Print the problem for debugging
    print("Optimization Problem:")
    print(problem)

    # Solve the problem using COIN_CMD with explicit path=None
    try:
        problem.solve(COIN_CMD(path=None, msg=False))
        print(f"Solver Status: {LpStatus[problem.status]}")
    except Exception as error:
        print(f"Solver failed: {error}")
        raise

    # Return the lineup if optimal
    if LpStatus[problem.status] == "Optimal":
        line

