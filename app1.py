import streamlit as st
import pandas as pd
from pulp import LpMaximize, LpProblem, LpVariable, lpSum, COIN_CMD, LpStatus

# Load player data from a CSV file
@st.cache
def load_player_data(file_path):
    players = pd.read_csv(file_path)
    players.columns = players.columns.str.strip()  # Remove extra spaces in column names
    players = players.rename(columns={
        "Player": "name",
        "Position": "position",
        "Salary": "salary",
        "Minutes": "minutes",
        "Usage": "usage",
        "projection": "projection"
    })
    players["positions"] = players["position"].apply(lambda x: x.split("/") if "/" in x else [x])
    return players

# Generate projections based on user-defined weights
def generate_projections(players, minutes_weight, usage_weight):
    players["projection"] = (
        players["minutes"] * minutes_weight +
        players["usage"].fillna(0) * usage_weight
    )
    return players

# Function to optimize lineup
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

    # Solve the problem using COIN_CMD solver
    problem.solve(COIN_CMD(msg=False))

    # Return the lineup if optimal
    if LpStatus[problem.status] == "Optimal":
        lineup = players[players["name"].isin([key for key, var in player_vars.items() if var.value() == 1])]
        return lineup
    else:
        return None

# Streamlit app
st.title("NBA Lineup Optimizer")
st.sidebar.header("Settings")

# Input parameters
salary_cap = st.sidebar.number_input("Salary Cap", min_value=30000, max_value=100000, value=50000, step=5000)
roster_size = st.sidebar.number_input("Roster Size", min_value=1, max_value=10, value=8, step=1)
minutes_weight = st.sidebar.slider("Minutes Weight", 0.0, 1.0, 0.5)
usage_weight = st.sidebar.slider("Usage Weight", 0.0, 1.0, 0.5)

# File uploader for player data
uploaded_file = st.sidebar.file_uploader("Upload Player Data CSV", type="csv")

if uploaded_file:
    try:
        # Load and process player data
        players = load_player_data(uploaded_file)
        players = generate_projections(players, minutes_weight, usage_weight)
        st.write("### Player Pool with Projections")
        st.dataframe(players)

        # Optimize lineup
        if st.button("Optimize Lineup"):
            lineup = optimize_lineup(players, salary_cap, roster_size)
            if lineup is not None:
                st.write("### Optimal Lineup")
                st.dataframe(lineup)
                st.write(f"**Total Salary:** {lineup['salary'].sum()}")
                st.write(f"**Total Projected Points:** {lineup['projection'].sum()}")
            else:
                st.write("No valid lineup found. Adjust the salary cap or roster size.")
    except ValueError as e:
        st.error(f"Error processing player data: {e}")
else:
    st.info("Upload a CSV file to get started.")
