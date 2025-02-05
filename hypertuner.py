#!/usr/bin/env python3
"""
Interactive Optuna Optimization CLI Using a Dirichlet Distribution with Baseline Injection

This script optimizes a candidate allocation over six assets:
    VT, THNQ, UPRO, KMLM, GLD, and TLT
with minimum constraints:
  - VT must be at least 40%
  - THNQ must be at least 10%
  - UPRO must be at least 5%
and no minimum for KMLM, GLD, or TLT.

This is achieved by:
  1. Defining a baseline vector:
         baseline = [0.4, 0.1, 0.05, 0, 0, 0]
  2. Sampling a Dirichlet vector d (using the gamma/exponential trick) for all assets.
  3. Combining them as:
         p = baseline + (1 - sum(baseline)) * d,
     which ensures that VT ≥ 40%, THNQ ≥ 10%, and UPRO ≥ 5%.
     
The candidate allocation is rounded to 4 decimals and printed as percentages.
When printing, the printed precision is (precision-2) decimals.
The loss function is defined as:
    loss = -sharpe + max(0, maxdrawdown/100 - 0.4)
Interactive input is requested for Sharpe and MaxDrawdown.
The optimization runs for 70 trials.
"""

# ===== USER EDITABLE SECTION =====

VARIABLES = {
    "names": ["VT", "THNQ", "UPRO", "KMLM", "GLD", "TLT"],
    "precision": 4  # Internal precision (4 decimals); printed percentages use (precision-2) decimals.
}

def loss_function(sharpe, maxdrawdown):
    """
    Loss function to be minimized.

    Parameters:
      - sharpe: The Sharpe ratio (higher is better).
      - maxdrawdown: The maximum drawdown (entered as a percentage, e.g., 20 for 20%).

    Returns:
      - The computed loss.
    """
    return -sharpe + max(0, maxdrawdown / 100 - 0.4)

# ===== END OF USER EDITABLE SECTION =====


# ===== OPTUNA OPTIMIZATION SECTION (DO NOT EDIT) =====

import numpy as np
import optuna
import math

def round_probabilities(p, digits=4):
    """
    Round a list of probabilities to a fixed number of decimals while ensuring they sum exactly to 1.
    
    This uses a largest‑remainder method.
    """
    scale = 10 ** digits
    floor_vals = [int(math.floor(prob * scale)) for prob in p]
    remainders = [prob * scale - fv for prob, fv in zip(p, floor_vals)]
    total_floor = sum(floor_vals)
    deficit = scale - total_floor  # Remaining units to distribute
    
    indices = sorted(range(len(p)), key=lambda i: remainders[i], reverse=True)
    for i in range(deficit):
        floor_vals[indices[i]] += 1
    return [val / scale for val in floor_vals]

def objective(trial):
    """
    Optuna objective function.
    
    Sampling procedure:
      1. Define a baseline vector:
           baseline[VT] = 0.4, baseline[THNQ] = 0.1, baseline[UPRO] = 0.05,
           and 0 for KMLM, GLD, and TLT.
         (Asset order: VT, THNQ, UPRO, KMLM, GLD, TLT)
      2. The total baseline sum is 0.4 + 0.1 + 0.05 = 0.55.
      3. Sample a Dirichlet vector d for all assets using the gamma (exponential) trick:
           For each asset, sample u in (1e-8, 1) and compute x = -log(u),
           then set d_i = x_i / sum(x).
      4. The candidate allocation is:
           p = baseline + (1 - sum(baseline)) * d,
         which ensures VT ≥ 40%, THNQ ≥ 10%, and UPRO ≥ 5%.
    
    The candidate is rounded to the desired precision, saved as trial attributes,
    and displayed as percentages (with (precision-2) decimals).
    
    The function then prompts for Sharpe and MaxDrawdown, confirms the input,
    and computes the loss.
    """
    n = len(VARIABLES["names"])
    # Define baseline: VT = 0.4, THNQ = 0.1, UPRO = 0.05, others = 0.
    baseline = np.zeros(n)
    baseline[0] = 0.4    # VT
    baseline[1] = 0.1    # THNQ
    baseline[2] = 0.05   # UPRO
    sum_baseline = np.sum(baseline)  # = 0.55

    # Sample a Dirichlet vector using the gamma trick.
    d = []
    for i in range(n):
        u = trial.suggest_float(f"u_{i}", 1e-8, 1.0)
        d.append(-math.log(u))
    d = np.array(d)
    d = d / d.sum()
    
    # Candidate allocation with minimum constraints.
    p = baseline + (1 - sum_baseline) * d  # p sums to 1.
    p_trim = round_probabilities(p, digits=VARIABLES["precision"])
    
    # Save candidate probabilities as trial attributes.
    for i, name in enumerate(VARIABLES["names"]):
        trial.set_user_attr(f"p_{i}", p_trim[i])
    
    # Display candidate allocation as percentages.
    print("\n=========================================")
    print("Trial candidate allocation (percentages):")
    for i, name in enumerate(VARIABLES["names"]):
        # Printed percentage precision uses VARIABLES['precision']-2 decimals.
        print(f"{name}: {p_trim[i]*100:.{VARIABLES['precision']-2}f}%")
    print("Sum:", f"{sum(p_trim)*100:.{VARIABLES['precision']-2}f}%")
    print("=========================================")
    
    # Interactive input with confirmation.
    while True:
        try:
            sharpe = float(input("Enter Sharpe: "))
        except ValueError:
            print("Invalid input for Sharpe. Please enter a numeric value.")
            continue
        try:
            maxdrawdown = float(input("Enter MaxDrawdown (as a percentage, e.g., 20 for 20%): "))
        except ValueError:
            print("Invalid input for MaxDrawdown. Please enter a numeric value.")
            continue
        print(f"\nYou entered:")
        print(f"  Sharpe: {sharpe}")
        print(f"  MaxDrawdown: {maxdrawdown}")
        confirm = input("Are these values correct? (Y/n/back): ").strip().lower()
        if confirm in ("y", "yes", ""):
            break
        elif confirm in ("n", "no", "back", "b"):
            print("Let's re-enter the values.\n")
            continue
        else:
            print("Invalid response. Please answer with 'Y' or 'n'.")
            continue

    loss = loss_function(sharpe, maxdrawdown)
    print(f"Computed Loss: {loss}\n")
    return loss

def main():
    print("Starting interactive optimization using a Dirichlet distribution with baseline injection...")
    print("Assets:", ", ".join(VARIABLES["names"]))
    print("Minimum constraints: VT >= 40%, THNQ >= 10%, UPRO >= 5%")
    print("No minimum for KMLM, GLD, and TLT.")
    print("Optimization will run for 70 trials. Provide Sharpe and MaxDrawdown as prompted.\n")
    
    study = optuna.create_study(direction="minimize")
    study.optimize(objective, n_trials=70)
    
    best_trial = study.best_trial
    print("\n===== Best Candidate After 70 Trials =====")
    print(f"Loss: {best_trial.value}")
    
    # Reconstruct the candidate distribution from best_trial.
    n = len(VARIABLES["names"])
    baseline = np.zeros(n)
    baseline[0] = 0.4    # VT
    baseline[1] = 0.1    # THNQ
    baseline[2] = 0.05   # UPRO
    sum_baseline = baseline.sum()
    
    d = []
    for i in range(n):
        u = best_trial.params.get(f"u_{i}")
        d.append(-math.log(u))
    d = np.array(d)
    d = d / d.sum()
    p_all = baseline + (1 - sum_baseline) * d
    p_trim = round_probabilities(p_all, digits=VARIABLES["precision"])
    
    for i, name in enumerate(VARIABLES["names"]):
        print(f"{name}: {p_trim[i]*100:.{VARIABLES['precision']-2}f}%")
    print("Sum:", f"{sum(p_trim)*100:.{VARIABLES['precision']-2}f}%")
    print("=========================================")

if __name__ == "__main__":
    main()
