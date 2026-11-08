"""
Phase 7 - builds the Supplier Dashboard as ONE self-contained HTML file:
    dashboard/supplier_dashboard.html
Double-click it to open in any browser. No internet or installs needed.

It reads the Phase 5 / Phase 6 outputs (run those scripts first), recomputes
the per-batch stock targets for every scenario/method with the SAME formula as
src/phase6_reorder_engine.py, and checks the yearly costs match that script's
saved table before writing anything.
"""
import json
from statistics import NormalDist
import numpy as np
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "reports" / "docs"
OUT = Path(__file__).resolve().parent / "supplier_dashboard.html"

# Same assumptions as phase6_reorder_engine.py
UNIT_COST, HOLD_RATE, LANDINGS_PER_YEAR, BATCH = 4_320_000, 0.25, 2000, 200
PERIODS_PER_YEAR = LANDINGS_PER_YEAR / BATCH
HOLD_PER_UNIT_PERIOD = UNIT_COST * HOLD_RATE * BATCH / LANDINGS_PER_YEAR
METHODS = {"LightGBM": "lgb_pred", "Random Forest": "rf_pred", "Constant baseline": "fair_baseline"}

bt = pd.read_csv(DOCS / "phase5_batch_predictions.csv")
aog = pd.read_csv(DOCS / "aog_cost_scenarios.csv")
aog["name"] = aog["scenario"].str.split(r"\s", regex=True).str[0]
policy = pd.read_csv(DOCS / "phase6_policy_comparison.csv")
eoq = pd.read_csv(DOCS / "phase6_order_size_eoq.csv")
rules = pd.read_csv(DOCS / "apriori_rules.csv")


def sigma_other_folds(col):
    err = bt["actual"] - bt[col]
    out = np.zeros(len(bt))
    for f in bt["fold"].unique():
        m = bt["fold"] == f
        out[m] = err[~m].std(ddof=1)
    return out


targets, scen_info = {}, {}
for _, sc in aog.iterrows():
    short_cost = sc["exposure_per_event_inr"]
    service = short_cost / (short_cost + HOLD_PER_UNIT_PERIOD)
    z = NormalDist().inv_cdf(service)
    scen_info[sc["name"]] = {"aog_per_hr": sc["aog_cost_per_hr_inr"], "per_event": short_cost,
                             "service": service, "z": z}
    targets[sc["name"]] = {}
    for m, col in METHODS.items():
        t = np.ceil(bt[col] + z * sigma_other_folds(col))
        targets[sc["name"]][m] = t.astype(int).tolist()
        # consistency check against Phase 6's saved results
        spare = np.maximum(t - bt["actual"], 0).sum()
        mine = spare * HOLD_PER_UNIT_PERIOD / len(bt) * PERIODS_PER_YEAR
        saved = policy[(policy.scenario == sc["name"]) & (policy.method == m)]["holding_cost_inr_per_year"].iloc[0]
        assert abs(mine - saved) < 1, f"Mismatch with Phase 6 for {sc['name']}/{m}: {mine} vs {saved}"

data = {
    "batches": bt["batch"].tolist(),
    "actual": bt["actual"].astype(int).tolist(),
    "forecast": {m: bt[c].round(2).tolist() for m, c in METHODS.items()},
    "target": targets,
    "scenarios": scen_info,
    "costs": policy[["scenario", "method", "holding_cost_inr_per_year", "aog_cost_inr_per_year",
                     "total_cost_inr_per_year", "batches_with_shortage", "avg_safety_buffer_units"]]
             .to_dict("records"),
    "eoq": eoq[["method", "order_cost_inr", "eoq_units", "orders_per_year", "orders_per_batch",
                "annual_demand_units"]].to_dict("records"),
    "rules": rules[rules["confidence"] >= 0.7].sort_values("lift", ascending=False).to_dict("records"),
    "hold_per_unit_period": HOLD_PER_UNIT_PERIOD,
}

html = (Path(__file__).resolve().parent / "dashboard_template.html").read_text(encoding="utf-8")
html = html.replace("/*__DATA__*/null", json.dumps(data))
OUT.write_text(html, encoding="utf-8")
print(f"Checked against Phase 6 results: OK\nWrote {OUT}")
