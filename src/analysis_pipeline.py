"""
Midterm analysis pipeline: EDA, statistical baseline, ABC/XYZ classification,
Apriori companion-part mining, and AOG/holding cost business case (INR).
Reads data/processed/* (see generate_synthetic_data.py for the placeholder
source — swap for the real Kaggle CSVs once downloaded, same schema).
Writes all charts to reports/figures/ and tables to reports/docs/.
"""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from mlxtend.frequent_patterns import apriori, association_rules
from mlxtend.preprocessing import TransactionEncoder
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROC = ROOT / "data" / "processed"
FIG = ROOT / "reports" / "figures"
DOCS = ROOT / "reports" / "docs"
FIG.mkdir(parents=True, exist_ok=True)
DOCS.mkdir(parents=True, exist_ok=True)

NAVY = "#2f5872"
TEAL = "#3f8c9e"
AMBER = "#d98c3a"
GREY = "#8a94a3"
plt.rcParams.update({
    "figure.facecolor": "white", "axes.facecolor": "white",
    "axes.edgecolor": "#cfd6dd", "axes.grid": True, "grid.color": "#e7ebef",
    "grid.linewidth": 0.8, "font.size": 11, "axes.titleweight": "bold",
    "axes.titlesize": 13, "axes.spines.top": False, "axes.spines.right": False,
})

landing = pd.read_csv(PROC / "landing_summary_features.csv", parse_dates=["date"])
sensor = pd.read_csv(PROC / "landing_gear_sensor_timeseries.csv", parse_dates=["date"])
parts = pd.read_csv(PROC / "parts_master.csv")
maint = pd.read_csv(PROC / "maintenance_teardown_log.csv", parse_dates=["date"])

# ---------------------------------------------------------------------------
# EDA 1 — brake temperature by environment (the core motivating signal)
# ---------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(7, 4.2))
data = [landing.loc[landing.environment == e, "peak_brake_temp_c"] for e in ["temperate", "cold_snow"]]
bp = ax.boxplot(data, labels=["Temperate routes", "Cold / snow routes"], patch_artist=True, widths=0.5)
for patch, c in zip(bp["boxes"], [TEAL, AMBER]):
    patch.set_facecolor(c); patch.set_alpha(0.75)
ax.set_ylabel("Peak brake temperature (°C)")
ax.set_title("Peak brake temperature is materially higher on cold/snow routes")
fig.tight_layout(); fig.savefig(FIG / "01_env_brake_temp.png", dpi=160); plt.close(fig)

# ---------------------------------------------------------------------------
# EDA 2 — cumulative wear index vs flight cycle, sample aircraft
# ---------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(7.5, 4.2))
for tail, g in landing.groupby("tail_number"):
    g = g.sort_values("flight_cycle")
    ax.plot(g["flight_cycle"], g["cum_wear"], marker="o", markersize=3, linewidth=1.4, label=tail)
ax.axhline(6.0, color=AMBER, linestyle="--", linewidth=1.2, label="Replacement threshold")
ax.set_xlabel("Flight cycle"); ax.set_ylabel("Cumulative brake wear index")
ax.set_title("Cumulative wear accumulation by tail number")
ax.legend(fontsize=8, ncol=2, loc="upper left")
fig.tight_layout(); fig.savefig(FIG / "02_cumulative_wear.png", dpi=160); plt.close(fig)

# ---------------------------------------------------------------------------
# Baseline — moving-average demand forecast for the focus part (Brake Assembly)
# ---------------------------------------------------------------------------
maint["month"] = maint["date"].values.astype("datetime64[M]")
monthly_demand = maint.groupby("month").size().rename("actual_demand").to_frame()
monthly_demand = monthly_demand.asfreq("MS", fill_value=0)
monthly_demand["ma_3"] = monthly_demand["actual_demand"].rolling(3, min_periods=1).mean()
mae = (monthly_demand["actual_demand"] - monthly_demand["ma_3"]).abs().mean()

fig, ax = plt.subplots(figsize=(7.5, 4.2))
ax.plot(monthly_demand.index, monthly_demand["actual_demand"], marker="o", color=NAVY, label="Actual replacement events")
ax.plot(monthly_demand.index, monthly_demand["ma_3"], marker="s", color=AMBER, linestyle="--", label="3-month moving average (baseline)")
ax.set_ylabel("Brake Assembly replacements / month")
ax.set_title(f"Statistical baseline forecast — MAE = {mae:.2f} units/month")
ax.legend(fontsize=9)
fig.autofmt_xdate()
fig.tight_layout(); fig.savefig(FIG / "03_baseline_forecast.png", dpi=160); plt.close(fig)
monthly_demand.to_csv(DOCS / "baseline_monthly_demand.csv")

# ---------------------------------------------------------------------------
# ABC / XYZ dual-matrix classification
# ---------------------------------------------------------------------------
basket_lists = maint["parts_replaced"].str.split(";")
part_counts = basket_lists.explode().value_counts()

usage = []
for _, p in parts.iterrows():
    name = p["part_name"]
    monthly_qty = maint.assign(has_part=basket_lists.apply(lambda b: name in b))
    monthly_qty = monthly_qty[monthly_qty["has_part"]].groupby("month").size().reindex(monthly_demand.index, fill_value=0)
    annual_qty = monthly_qty.sum() * (12 / max(len(monthly_demand), 1))
    cv = monthly_qty.std() / monthly_qty.mean() if monthly_qty.mean() > 0 else np.nan
    usage.append({
        "part_name": name, "unit_cost_inr": p["unit_cost_inr"],
        "annual_qty": round(annual_qty, 1),
        "annual_value_inr": round(annual_qty * p["unit_cost_inr"], 0),
        "demand_cv": cv,
    })
abc_xyz = pd.DataFrame(usage).sort_values("annual_value_inr", ascending=False)
abc_xyz["cum_value_pct"] = abc_xyz["annual_value_inr"].cumsum() / abc_xyz["annual_value_inr"].sum() * 100
abc_xyz["abc_class"] = pd.cut(abc_xyz["cum_value_pct"], bins=[0, 80, 95, 100], labels=["A", "B", "C"])
abc_xyz["xyz_class"] = pd.cut(abc_xyz["demand_cv"].fillna(abc_xyz["demand_cv"].max()),
                               bins=[-0.01, 0.5, 1.0, 10], labels=["X", "Y", "Z"])
abc_xyz.to_csv(DOCS / "abc_xyz_classification.csv", index=False)

fig, ax = plt.subplots(figsize=(7.5, 5))
class_colors = {"A": NAVY, "B": TEAL, "C": GREY}
for _, r in abc_xyz.iterrows():
    ax.scatter(r["demand_cv"], r["annual_value_inr"] / 1e5, s=180,
               color=class_colors[r["abc_class"]], edgecolor="white", linewidth=1.2, zorder=3)
    ax.annotate(f"{r['part_name']}\n({r['abc_class']}{r['xyz_class']})",
                (r["demand_cv"], r["annual_value_inr"] / 1e5),
                textcoords="offset points", xytext=(8, 4), fontsize=8)
ax.axvline(0.5, color="#cfd6dd", linewidth=1); ax.axvline(1.0, color="#cfd6dd", linewidth=1)
ax.set_xlabel("Demand coefficient of variation  (X: stable → Z: erratic)")
ax.set_ylabel("Annual consumption value (₹ lakh)")
ax.set_title("ABC/XYZ dual-matrix classification of landing-gear spares")
fig.tight_layout(); fig.savefig(FIG / "04_abc_xyz_matrix.png", dpi=160); plt.close(fig)

# ---------------------------------------------------------------------------
# Apriori — companion-part co-replacement rules
# ---------------------------------------------------------------------------
te = TransactionEncoder()
te_data = te.fit(basket_lists).transform(basket_lists)
basket_df = pd.DataFrame(te_data, columns=te.columns_)
freq_items = apriori(basket_df, min_support=0.15, use_colnames=True)
rules = association_rules(freq_items, metric="lift", min_threshold=1.05)
rules = rules.sort_values("lift", ascending=False)
rules_out = rules[["antecedents", "consequents", "support", "confidence", "lift"]].copy()
rules_out["antecedents"] = rules_out["antecedents"].apply(lambda s: ", ".join(sorted(s)))
rules_out["consequents"] = rules_out["consequents"].apply(lambda s: ", ".join(sorted(s)))
rules_out.round(3).to_csv(DOCS / "apriori_rules.csv", index=False)

top_rules = rules_out.head(6).iloc[::-1]
fig, ax = plt.subplots(figsize=(7.5, 4.2))
labels = [f"{a} → {c}" for a, c in zip(top_rules["antecedents"], top_rules["consequents"])]
ax.barh(labels, top_rules["lift"], color=TEAL)
ax.set_xlabel("Lift"); ax.set_title("Top companion-part co-replacement rules (Apriori)")
fig.tight_layout(); fig.savefig(FIG / "05_apriori_rules.png", dpi=160); plt.close(fig)

# ---------------------------------------------------------------------------
# Business case — AOG cost exposure & holding cost, in INR
# ---------------------------------------------------------------------------
USD_TO_INR = 96.0
aog_cost_per_hr_usd = {"Low\n(narrowbody,\ndomestic)": 10_000, "Mid\n(narrowbody,\ntypical)": 45_000, "High\n(widebody,\npeak)": 150_000}
aog_hours_avoided = 18  # assumed average stockout-driven AOG duration avoided per prevented event
brake_unit_cost_inr = float(parts.loc[parts.part_name == "Brake Assembly", "unit_cost_inr"].iloc[0])

aog_rows = []
for label, usd_hr in aog_cost_per_hr_usd.items():
    inr_hr = usd_hr * USD_TO_INR
    exposure = inr_hr * aog_hours_avoided
    aog_rows.append({"scenario": label, "aog_cost_per_hr_inr": inr_hr, "exposure_per_event_inr": exposure})
aog_df = pd.DataFrame(aog_rows)
aog_df.to_csv(DOCS / "aog_cost_scenarios.csv", index=False)

holding_rate = 0.25  # 25%/yr, standard aerospace MRO rule-of-thumb (20-30% range)
avg_stock_units = 4
holding_cost_annual_inr = brake_unit_cost_inr * avg_stock_units * holding_rate

fig, ax = plt.subplots(figsize=(8.5, 4.6))
bars = ax.bar(aog_df["scenario"], aog_df["exposure_per_event_inr"] / 1e5, color=[GREY, TEAL, NAVY], width=0.55)
ax.axhline(holding_cost_annual_inr / 1e5, color=AMBER, linestyle="--", linewidth=1.4,
           label=f"Annual holding cost of 4 spare Brake Assemblies (₹{holding_cost_annual_inr/1e5:.1f} lakh)")
ax.set_ylabel("₹ lakh")
ax.set_title("Per-event AOG cost exposure vs. annual holding cost — Brake Assembly", fontsize=12)
ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.1f"))
ax.tick_params(axis="x", labelsize=9)
ax.legend(fontsize=8, loc="upper left")
fig.tight_layout(); fig.savefig(FIG / "06_business_case.png", dpi=160); plt.close(fig)

print("Wrote figures to", FIG)
print("Wrote tables to", DOCS)
print(f"\nBaseline MAE: {mae:.2f} units/month")
print(f"Holding cost (4 units, 25%/yr): INR {holding_cost_annual_inr:,.0f}")
print(abc_xyz[["part_name", "abc_class", "xyz_class", "annual_value_inr"]].to_string(index=False))
