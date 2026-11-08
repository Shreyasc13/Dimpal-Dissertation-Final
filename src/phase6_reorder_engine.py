"""
Phase 6 - Reorder-point engine for the Landing Gear Actuator, checked against
the AOG cost model.

Plain-English summary:
  * Each batch of 200 landings is one "planning period". Before the period
    starts, the shelf is topped up to a target level:
        target stock = forecast for the period + safety buffer
  * Safety buffer = z x (typical forecast error). The size of z comes from
    weighing the two costs against each other (the textbook "newsvendor" rule):
        - cost of being 1 unit short   = one AOG event (18 h x AOG rate/hour)
        - cost of 1 extra unit on shelf = unit cost x 25%/yr x (period / year)
      Target chance of NOT running out = short cost / (short cost + extra cost)
  * Then the 50 batches are replayed. For each method we count units short
    (each one = one AOG event, an assumption) and spare units left on the shelf,
    and turn both into rupees.
  * Methods compared:
        Constant baseline - forecast = training-batch average (no model)
        LightGBM          - forecast from Phase 5 (main model)
        Random Forest     - forecast from Phase 5 (comparison)
  * Fairness: for every batch, the "typical error" is measured only on the
    OTHER folds' batches, never on the batch being scored.

ASSUMPTIONS (invented, must be disclosed):
  - 2,000 landings/year  -> one batch of 200 = 0.1 year
  - Parts ordered for a batch arrive before that batch starts (lead time is
    covered by planning one batch ahead)
  - Each unit short = one separate AOG event of 18 hours
  - Unit cost Rs 43,20,000; holding cost 25% per year (same as midterm)
  - The forecast uses each landing's conditions (load, cycles...). In real use
    these would come from flight plans / known aircraft cycle counts.

Run phase5_lightgbm.py first.
"""
from statistics import NormalDist
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIG = ROOT / "reports" / "figures"
DOCS = ROOT / "reports" / "docs"

UNIT_COST = 4_320_000          # Rs, Landing Gear Actuator (assumed, as in midterm)
HOLD_RATE = 0.25               # per year
LANDINGS_PER_YEAR = 2000       # assumed fleet utilisation
BATCH = 200
PERIOD_YEARS = BATCH / LANDINGS_PER_YEAR
PERIODS_PER_YEAR = LANDINGS_PER_YEAR / BATCH
HOLD_PER_UNIT_PERIOD = UNIT_COST * HOLD_RATE * PERIOD_YEARS   # Rs 1,08,000

NAVY, TEAL, AMBER, GREY = "#2f5872", "#3f8c9e", "#d98c3a", "#8a94a3"
plt.rcParams.update({
    "figure.facecolor": "white", "axes.facecolor": "white",
    "axes.edgecolor": "#cfd6dd", "axes.grid": True, "grid.color": "#e7ebef",
    "font.size": 11, "axes.titleweight": "bold", "axes.titlesize": 13,
    "axes.spines.top": False, "axes.spines.right": False,
})

bt = pd.read_csv(DOCS / "phase5_batch_predictions.csv")
aog = pd.read_csv(DOCS / "aog_cost_scenarios.csv")
aog["name"] = aog["scenario"].str.split(r"\s", regex=True).str[0]   # "Low", "Mid", "High"

METHODS = {"Constant baseline": "fair_baseline", "LightGBM": "lgb_pred", "Random Forest": "rf_pred"}


def sigma_from_other_folds(col):
    """Typical forecast error for each batch, measured only on the other folds."""
    err = bt["actual"] - bt[col]
    out = np.zeros(len(bt))
    for f in bt["fold"].unique():
        mask = bt["fold"] == f
        out[mask] = err[~mask].std(ddof=1)
    return out


rows, policy_rows = [], []
for _, sc in aog.iterrows():
    short_cost = sc["exposure_per_event_inr"]
    service = short_cost / (short_cost + HOLD_PER_UNIT_PERIOD)    # newsvendor ratio
    z = NormalDist().inv_cdf(service)
    for mname, col in METHODS.items():
        sigma = sigma_from_other_folds(col)
        target = np.ceil(bt[col] + z * sigma)                       # whole units on shelf
        short = np.maximum(bt["actual"] - target, 0)
        spare = np.maximum(target - bt["actual"], 0)
        hold_cost = spare.sum() * HOLD_PER_UNIT_PERIOD
        aog_cost = short.sum() * short_cost
        rows.append({
            "scenario": sc["name"], "method": mname,
            "target_service_level": service, "z": z,
            "avg_safety_buffer_units": float((target - bt[col]).mean()),
            "batches_with_shortage": int((short > 0).sum()),
            "units_short_total": int(short.sum()),
            "avg_spare_units_per_batch": float(spare.mean()),
            "holding_cost_inr_per_year": hold_cost / len(bt) * PERIODS_PER_YEAR,
            "aog_cost_inr_per_year": aog_cost / len(bt) * PERIODS_PER_YEAR,
        })
        if sc["name"] == "Mid":
            policy_rows.append(pd.DataFrame({
                "batch": bt["batch"], "method": mname, "forecast": bt[col],
                "target_stock": target, "actual_demand": bt["actual"],
                "units_short": short, "spare_units": spare}))

res = pd.DataFrame(rows)
res["total_cost_inr_per_year"] = res["holding_cost_inr_per_year"] + res["aog_cost_inr_per_year"]
res.to_csv(DOCS / "phase6_policy_comparison.csv", index=False)
pd.concat(policy_rows).to_csv(DOCS / "phase6_batch_decisions_mid.csv", index=False)

# ---------------------------------------------------------------------------
# Charts
# ---------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(10, 4.6))
scen = list(aog["name"])
w = 0.26
colors = {"Constant baseline": GREY, "LightGBM": AMBER, "Random Forest": TEAL}
for i, m in enumerate(METHODS):
    vals = [res[(res.scenario == s) & (res.method == m)]["total_cost_inr_per_year"].iloc[0] / 1e7 for s in scen]
    bars = ax.bar(np.arange(len(scen)) + (i - 1) * w, vals, w, label=m, color=colors[m])
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.03, f"{v:.2f}", ha="center", fontsize=8)
ax.set_xticks(np.arange(len(scen)))
ax.set_xticklabels([f"{s} AOG scenario" for s in scen])
ax.set_ylabel("Rs crore per year (holding + AOG)")
ax.set_title("Phase 6: yearly stock cost by method - Landing Gear Actuator")
ax.legend(fontsize=9)
fig.savefig(FIG / "10_phase6_total_cost.png", dpi=160, bbox_inches="tight")
plt.close(fig)

mid = pd.concat(policy_rows)
fig, ax = plt.subplots(figsize=(11, 4.6))
ax.plot(bt["batch"], bt["actual"], "o-", color=NAVY, ms=4, label="Actual demand")
for m, st in [("Constant baseline", ":"), ("LightGBM", "--")]:
    d = mid[mid.method == m]
    ax.step(d["batch"], d["target_stock"], where="mid", ls=st, color=colors[m], lw=2,
            label=f"Stock kept on shelf - {m}")
ax.set_xlabel("Batch of 200 landings")
ax.set_ylabel("Landing Gear Actuator units")
ax.set_title("Phase 6: how much stock each method keeps (Mid AOG scenario)")
ax.legend(fontsize=9, loc="lower right")
fig.savefig(FIG / "11_phase6_stock_levels.png", dpi=160, bbox_inches="tight")
plt.close(fig)

# ---------------------------------------------------------------------------
pd.set_option("display.width", 200)
show = res.copy()
for c in ["holding_cost_inr_per_year", "aog_cost_inr_per_year", "total_cost_inr_per_year"]:
    show[c] = (show[c] / 1e7).round(2)
show = show.rename(columns={"holding_cost_inr_per_year": "hold_cr/yr", "aog_cost_inr_per_year": "aog_cr/yr",
                            "total_cost_inr_per_year": "total_cr/yr", "target_service_level": "service"})
print(f"Holding cost of 1 extra unit for one batch: Rs {HOLD_PER_UNIT_PERIOD:,.0f}")
print(show.round({"service": 4, "z": 2, "avg_safety_buffer_units": 1, "avg_spare_units_per_batch": 1}).to_string(index=False))
