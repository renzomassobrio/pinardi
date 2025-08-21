import pandas as pd
from ortools.sat.python import cp_model

# --- Solve cutting stock problem ---
def cutting_stock_with_kerf(stock_length, pieces, kerf=0.0):
    n_pieces = len(pieces)
    max_bars = n_pieces  # worst case: one piece per bar
    scale = 1000
    stock_length_int = int(stock_length * scale)
    kerf_int = int(kerf * scale)
    pieces_int = [int(p * scale) for p in pieces]

    model = cp_model.CpModel()

    # x[i][j] = 1 if piece i is cut from bar j
    x = [[model.NewBoolVar(f"x_{i}_{j}") for j in range(max_bars)] for i in range(n_pieces)]
    # y[j] = 1 if bar j is used
    y = [model.NewBoolVar(f"y_{j}") for j in range(max_bars)]

    # each piece must be assigned to exactly one bar
    for i in range(n_pieces):
        model.Add(sum(x[i][j] for j in range(max_bars)) == 1)

    # bar capacity + linking constraints
    for j in range(max_bars):
        pieces_sum = sum(x[i][j] * pieces_int[i] for i in range(n_pieces))
        count = sum(x[i][j] for i in range(n_pieces))

        # capacity constraint
        model.Add(pieces_sum + kerf_int * (count - 1) <= stock_length_int)

        # link y[j] with usage
        model.Add(count >= y[j])                # if bar is used, at least one piece
        model.Add(count <= n_pieces * y[j])     # if bar not used, no pieces

    # minimize number of bars used
    model.Minimize(sum(y))

    # solve
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 30  # safeguard for large instances
    status = solver.Solve(model)

    if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
        bars = [[] for _ in range(max_bars)]
        for i in range(n_pieces):
            for j in range(max_bars):
                if solver.Value(x[i][j]):
                    bars[j].append(pieces[i])
        bars = [b for b in bars if b]  # remove empties
        return bars
    else:
        return None

