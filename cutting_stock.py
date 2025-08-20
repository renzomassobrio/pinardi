import pandas as pd
from ortools.sat.python import cp_model

# --- Solve cutting stock problem ---
def cutting_stock_with_kerf(stock_length, pieces, kerf=0.0):
    n_pieces = len(pieces)
    max_bars = n_pieces
    scale = 1000
    stock_length_int = int(stock_length * scale)
    kerf_int = int(kerf * scale)
    pieces_int = [int(p*scale) for p in pieces]

    model = cp_model.CpModel()
    x = [[model.NewBoolVar(f"x_{i}_{j}") for j in range(max_bars)] for i in range(n_pieces)]
    y = [model.NewBoolVar(f"y_{j}") for j in range(max_bars)]

    for i in range(n_pieces):
        model.Add(sum(x[i][j] for j in range(max_bars)) == 1)

    for j in range(max_bars):
        pieces_sum = sum(x[i][j]*pieces_int[i] for i in range(n_pieces))
        count = sum(x[i][j] for i in range(n_pieces))
        model.Add(pieces_sum + kerf_int*(count-1) <= stock_length_int).OnlyEnforceIf(y[j])
        model.Add(count > 0).OnlyEnforceIf(y[j])
        model.Add(count == 0).OnlyEnforceIf(y[j].Not())

    model.Minimize(sum(y))

    solver = cp_model.CpSolver()
    status = solver.Solve(model)

    if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
        bars = [[] for _ in range(max_bars)]
        for i in range(n_pieces):
            for j in range(max_bars):
                if solver.Value(x[i][j]):
                    bars[j].append(pieces[i])
        bars = [b for b in bars if b]
        return bars
    else:
        return None
