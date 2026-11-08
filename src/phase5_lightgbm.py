"""
Phase 5 - LightGBM demand forecast for the Landing Gear Actuator.

Plain-English summary of what this script does:
  1. Every landing gets a "chance of actuator failure" from the model,
     based only on its 8 operating conditions (load, braking force, ...).
     The other 3 failure flags are NOT used as inputs: on a real day you
     would not know them in advance, so using them would be cheating.
  2. Landings are grouped into the same 50 batches of 200 used by the
     baseline. Adding up the chances in a batch = predicted actuators
     needed for that batch.
  3. Fair test: the batches are split into 5 groups ("folds"). The model
     is trained on 4 groups and tested on the 5th, which it never saw.
     Repeated 5 times so every batch is tested exactly once.
  4. Tuning: inside each training set, a small grid of settings is tried
     (again with held-out data) and the best one is used. The test batches
     are never used to pick settings.
  5. Compared against:
       - the original baseline (MAE 5.52; it used the average of ALL 50
         batches, including the ones it was scored on)
       - a "fair" baseline: the average from the training batches only
       - Random Forest, tested the same way.

Run load_real_data.py first. Outputs go to reports/docs/ and reports/figures/.
"""
import itertools
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path
from lightgbm import LGBMClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import KFold
from sklearn.metrics import log_loss, roc_auc_score

ROOT = Path(__file__).resolve().parent.parent
PROC = ROOT / "data" / "processed"
FIG = ROOT / "reports" / "figures"
DOCS = ROOT / "reports" / "docs"
FIG.mkdir(parents=True, exist_ok=True)
DOCS.mkdir(parents=True, exist_ok=True)

SEED = 42
BATCH = 200
TARGET = "shock_absorber_failure"  # Landing Gear Actuator
NUM = ["landing_cycles", "load_during_landing", "taxiing_duration",
       "speed_during_landing", "braking_force", "tire_pressure", "hydraulic_pressure"]
CAT = "runway_condition"

NAVY, TEAL, AMBER, GREY = "#2f5872", "#3f8c9e", "#d98c3a", "#8a94a3"
plt.rcParams.update({
    "figure.facecolor": "white", "axes.facecolor": "white",
    "axes.edgecolor": "#cfd6dd", "axes.grid": True, "grid.color": "#e7ebef",
    "font.size": 11, "axes.titleweight": "bold", "axes.titlesize": 13,
    "axes.spines.top": False, "axes.spines.right": False,
})

# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------
df = pd.read_csv(PROC / "landing_events.csv")
df["batch"] = np.arange(len(df)) // BATCH          # same sequential batches as the baseline
n_batches = df["batch"].nunique()
y = df[TARGET].values

X_lgb = df[NUM + [CAT]].copy()
X_lgb[CAT] = X_lgb[CAT].astype("category")         # LightGBM handles categories natively
X_rf = pd.get_dummies(df[NUM + [CAT]], columns=[CAT], dtype=float)  # RF needs one-hot

actual = df.groupby("batch")[TARGET].sum().values
original_baseline_mae = np.abs(actual - actual.mean()).mean()

# ---------------------------------------------------------------------------
# Tuning grids (kept small and standard - not hunted for a result)
# ---------------------------------------------------------------------------
LGB_GRID = [dict(num_leaves=nl, learning_rate=lr, n_estimators=ne, min_child_samples=20)
            for nl, lr, ne in itertools.product([7, 15, 31], [0.03, 0.1], [100, 300])]
RF_GRID = [dict(n_estimators=300, min_samples_leaf=leaf, max_features=mf)
           for leaf, mf in itertools.product([1, 5, 20], ["sqrt", 0.6])]


def make_lgb(p):
    return LGBMClassifier(**p, random_state=SEED, verbose=-1)


def make_rf(p):
    return RandomForestClassifier(**p, random_state=SEED, n_jobs=-1)


def tune(make, grid, X, y_, groups):
    """Pick the setting with the lowest held-out log-loss, using only training batches."""
    inner = KFold(n_splits=4, shuffle=True, random_state=SEED)
    ub = np.unique(groups)
    best, best_score = None, np.inf
    for p in grid:
        losses = []
        for tr_b, va_b in inner.split(ub):
            tr = np.isin(groups, ub[tr_b]); va = ~tr
            m = make(p).fit(X[tr], y_[tr])
            losses.append(log_loss(y_[va], m.predict_proba(X[va])[:, 1], labels=[0, 1]))
        s = float(np.mean(losses))
        if s < best_score:
            best, best_score = p, s
    return best


# ---------------------------------------------------------------------------
# Outer 5-fold test over batches
# ---------------------------------------------------------------------------
outer = KFold(n_splits=5, shuffle=True, random_state=SEED)
batch_ids = np.arange(n_batches)
groups = df["batch"].values

oof = {"lgb": np.zeros(len(df)), "rf": np.zeros(len(df))}
fair_base_pred = np.zeros(n_batches)
fold_of_batch = np.zeros(n_batches, dtype=int)
chosen = []

for fold, (tr_b, te_b) in enumerate(outer.split(batch_ids), start=1):
    tr = np.isin(groups, tr_b); te = ~tr
    fold_of_batch[te_b] = fold

    # fair baseline: average failure rate of the TRAINING landings x 200
    fair_base_pred[te_b] = y[tr].mean() * BATCH

    # LightGBM keeps the DataFrame so runway_condition stays a category column
    Xl_tr, Xl_te = X_lgb[tr], X_lgb[te]
    p_lgb = tune(make_lgb, LGB_GRID, Xl_tr.reset_index(drop=True), y[tr], groups[tr])
    oof["lgb"][te] = make_lgb(p_lgb).fit(Xl_tr, y[tr]).predict_proba(Xl_te)[:, 1]

    Xr_tr, Xr_te = X_rf[tr].values, X_rf[te].values
    p_rf = tune(make_rf, RF_GRID, Xr_tr, y[tr], groups[tr])
    oof["rf"][te] = make_rf(p_rf).fit(Xr_tr, y[tr]).predict_proba(Xr_te)[:, 1]

    chosen.append({"fold": fold, "test_batches": " ".join(map(str, sorted(te_b))),
                   "lgb_params": str(p_lgb), "rf_params": str(p_rf)})
    print(f"fold {fold} done  LGB={p_lgb}  RF={p_rf}")

# ---------------------------------------------------------------------------
# Batch-level results
# ---------------------------------------------------------------------------
df["p_lgb"], df["p_rf"] = oof["lgb"], oof["rf"]
bt = df.groupby("batch").agg(actual=(TARGET, "sum"), lgb_pred=("p_lgb", "sum"),
                             rf_pred=("p_rf", "sum"))
bt["fold"] = fold_of_batch
bt["original_baseline"] = actual.mean()
bt["fair_baseline"] = fair_base_pred

mae = lambda col: float(np.abs(bt["actual"] - bt[col]).mean())

# IMPORTANT CHECK: the Kaggle file is SIMULATED data. The actuator flag follows
# an exact rule: failure = load > 70 OR landing_cycles > 401. If this rule
# matches every landing, the best possible error is 0 - there is no randomness
# left to predict - and the model is simply rediscovering the simulator's rule.
rule = ((df["load_during_landing"] > 70) | (df["landing_cycles"] > 401)).astype(int)
rule_matches = int((rule == df[TARGET]).sum())
print(f"Simulator-rule check: 'load > 70 OR cycles > 401' matches {rule_matches} of {len(df)} landings")

results = pd.DataFrame([
    {"method": "Original baseline (all-batch average, as in midterm report)", "batch_MAE": original_baseline_mae},
    {"method": "Fair baseline (training-batch average only)", "batch_MAE": mae("fair_baseline")},
    {"method": "Random Forest (tuned, tested on unseen batches)", "batch_MAE": mae("rf_pred")},
    {"method": "LightGBM (tuned, tested on unseen batches)", "batch_MAE": mae("lgb_pred")},
])
landing_metrics = pd.DataFrame([
    {"model": "LightGBM", "AUC": roc_auc_score(y, oof["lgb"]), "log_loss": log_loss(y, oof["lgb"])},
    {"model": "Random Forest", "AUC": roc_auc_score(y, oof["rf"]), "log_loss": log_loss(y, oof["rf"])},
])

# ---------------------------------------------------------------------------
# Feature importance: refit LightGBM on all data with the most-chosen setting
# ---------------------------------------------------------------------------
most_common = pd.Series([c["lgb_params"] for c in chosen]).mode()[0]
final = make_lgb(eval(most_common)).fit(X_lgb, y)
imp = pd.Series(final.booster_.feature_importance("gain"), index=NUM + [CAT])
imp = (imp / imp.sum() * 100).sort_values(ascending=False)

# ---------------------------------------------------------------------------
# Save tables
# ---------------------------------------------------------------------------
results.to_csv(DOCS / "phase5_results.csv", index=False)
landing_metrics.to_csv(DOCS / "phase5_landing_metrics.csv", index=False)
bt.reset_index().to_csv(DOCS / "phase5_batch_predictions.csv", index=False)
imp.rename("gain_pct").to_csv(DOCS / "phase5_feature_importance.csv")
pd.DataFrame(chosen).to_csv(DOCS / "phase5_chosen_settings.csv", index=False)

# ---------------------------------------------------------------------------
# Charts
# ---------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(11, 4.6))
ax.plot(bt.index, bt["actual"], "o-", color=NAVY, ms=4, label="Actual replacements")
ax.plot(bt.index, bt["lgb_pred"], "s--", color=AMBER, ms=4,
        label=f"LightGBM forecast (MAE {mae('lgb_pred'):.2f})")
ax.axhline(actual.mean(), color=GREY, ls=":",
           label=f"Constant baseline (MAE {original_baseline_mae:.2f})")
ax.set_xlabel("Batch of 200 landings (each tested on a model that never saw it)")
ax.set_ylabel("Landing Gear Actuator units")
ax.set_title("Phase 5: LightGBM forecast vs. actual vs. baseline")
ax.legend(loc="lower right", fontsize=9)
fig.savefig(FIG / "07_phase5_forecast_vs_actual.png", dpi=160, bbox_inches="tight")
plt.close(fig)

fig, ax = plt.subplots(figsize=(9, 4.4))
labels = ["Original\nbaseline", "Fair\nbaseline", "Random\nForest", "LightGBM"]
colors = [GREY, GREY, TEAL, AMBER]
bars = ax.bar(labels, results["batch_MAE"], color=colors, width=0.6)
for b, v in zip(bars, results["batch_MAE"]):
    ax.text(b.get_x() + b.get_width() / 2, v + 0.08, f"{v:.2f}", ha="center", fontsize=10)
ax.set_ylabel("Average error (units per batch)  - lower is better")
ax.set_title("Phase 5: forecast error per batch of 200 landings")
fig.savefig(FIG / "08_phase5_mae_comparison.png", dpi=160, bbox_inches="tight")
plt.close(fig)

fig, ax = plt.subplots(figsize=(8, 4.2))
imp.sort_values().plot.barh(ax=ax, color=TEAL)
ax.set_xlabel("Share of model's learning (gain, %)")
ax.set_title("What LightGBM relies on - Landing Gear Actuator")
fig.savefig(FIG / "09_phase5_feature_importance.png", dpi=160, bbox_inches="tight")
plt.close(fig)

# ---------------------------------------------------------------------------
print("\n=== Batch-level error (units per batch of 200 landings) ===")
print(results.to_string(index=False, float_format=lambda v: f"{v:.2f}"))
print("\n=== Per-landing quality (unseen batches) ===")
print(landing_metrics.to_string(index=False, float_format=lambda v: f"{v:.3f}"))
print("\n=== LightGBM feature importance (gain %) ===")
print(imp.round(1).to_string())
print(f"\nMost-chosen LightGBM setting: {most_common}")
