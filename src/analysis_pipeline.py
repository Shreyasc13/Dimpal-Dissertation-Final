"""
Midterm analysis pipeline, rebuilt against the REAL Kaggle dataset
(10,000 landing records — see load_real_data.py). Run load_real_data.py
first. Produces EDA, a base-rate baseline, ABC/XYZ classification,
Apriori companion-part mining, and the AOG/holding cost business case (INR).
Writes charts to reports/figures/ and tables to reports/docs/.
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

NAVY, TEAL, AMBER, GREY = "#2f5872", "#3f8c9e", "#d98c3a", "#8a94a3"
plt.rcParams.update({
    "figure.facecolor": "white", "axes.facecolor": "white",
    "axes.edgecolor": "#cfd6dd", "axes.grid": True, "grid.color": "#e7ebef",
    "grid.linewidth": 0.8, "font.size": 11, "axes.titleweight": "bold",
    "axes.titlesize": 13, "axes.spines.top": False, "axes.spines.right": False,
})

df = pd.read_csv(PROC / "landing_events.csv")
parts = pd.read_csv(PROC / "parts_master.csv")

PART_MAP = dict(zip(parts["part_id"], parts["part_name"]))
FLAGS = list(PART_MAP.keys())
NUM_FEATURES = ["landing_cycles", "load_during_landing", "taxiing_duration",
                 "speed_during_landing", "braking_force", "tire_pressure", "hydraulic_pressure"]

# ---------------------------------------------------------------------------
# EDA 1 — what actually predicts failure: runway condition vs operating severity
# ---------------------------------------------------------------------------
fig, axes = plt.subplots(1, 2, figsize=(11, 4.4))

TARGET_FLAG = "shock_absorber_failure"  # Landing Gear Actuator — the real AX-class focus part
rc_rates = df.groupby("runway_condition")[TARGET_FLAG].mean().reindex(["dry", "wet", "snowy"])
axes[0].bar(rc_rates.index, rc_rates.values * 100, color=[TEAL, "#5a9fb0", NAVY], width=0.55)
axes[0].set_ylim(50, 70)
axes[0].set_ylabel("Landing Gear Actuator failure rate (%)")
axes[0].set_title("By runway condition\n(barely moves)", fontsize=11)

LOAD_LABELS = ["Lightest\n20%", "2nd\nlightest", "Middle\n20%", "2nd\nheaviest", "Heaviest\n20%"]
df["load_q"] = pd.qcut(df["load_during_landing"], 5, labels=LOAD_LABELS)
ld_rates = df.groupby("load_q", observed=True)[TARGET_FLAG].mean().reindex(LOAD_LABELS)
axes[1].bar(ld_rates.index.astype(str), ld_rates.values * 100, color=AMBER, width=0.55)
axes[1].set_ylim(0, 100)
axes[1].set_ylabel("Landing Gear Actuator failure rate (%)")
axes[1].set_title("By landing weight, lightest to heaviest\n(strong upward trend)", fontsize=11)

fig.suptitle("What actually drives Landing Gear Actuator failure: landing load, not weather", fontsize=13, fontweight="bold", y=1.03)
fig.tight_layout()
fig.savefig(FIG / "01_env_brake_temp.png", dpi=160, bbox_inches="tight")
plt.close(fig)

# ---------------------------------------------------------------------------
# EDA 2 — correlation of each operating factor with each part's failure flag
# ---------------------------------------------------------------------------
corr = df[NUM_FEATURES + FLAGS].corr().loc[NUM_FEATURES, FLAGS]
corr.columns = [PART_MAP[c] for c in corr.columns]

fig, ax = plt.subplots(figsize=(8.5, 5))
im = ax.imshow(corr.values, cmap="RdBu_r", vmin=-0.85, vmax=0.85, aspect="auto")
ax.set_xticks(range(len(corr.columns))); ax.set_xticklabels(corr.columns, rotation=20, ha="right")
ax.set_yticks(range(len(corr.index))); ax.set_yticklabels(corr.index)
for i in range(corr.shape[0]):
    for j in range(corr.shape[1]):
        v = corr.values[i, j]
        ax.text(j, i, f"{v:.2f}", ha="center", va="center", fontsize=9,
                color="white" if abs(v) > 0.45 else "#222")
ax.set_title("Which operating factors predict which part's failure")
fig.colorbar(im, ax=ax, fraction=0.04, pad=0.03, label="Correlation")
fig.tight_layout()
fig.savefig(FIG / "02_cumulative_wear.png", dpi=160)
plt.close(fig)

# ---------------------------------------------------------------------------
# Baseline — the file has no dates/aircraft IDs, so landings are grouped into
# sequential batches of 200 (NOT calendar months) purely to get a repeatable
# "period" for a baseline-vs-actual comparison (see Section 9 for this caveat)
# ---------------------------------------------------------------------------
BATCH_SIZE = 200
df["batch"] = np.arange(len(df)) // BATCH_SIZE
batch_counts = df.groupby("batch")[FLAGS].sum()
batch_counts.columns = [PART_MAP[c] for c in batch_counts.columns]

FOCUS_PART = "Landing Gear Actuator"
baseline_pred = batch_counts[FOCUS_PART].mean()
mae = (batch_counts[FOCUS_PART] - baseline_pred).abs().mean()

fig, ax = plt.subplots(figsize=(7.5, 4.2))
ax.plot(batch_counts.index, batch_counts[FOCUS_PART], marker="o", markersize=3, color=NAVY, label="Actual replacements per batch")
ax.axhline(baseline_pred, color=AMBER, linestyle="--", linewidth=1.4, label=f"Constant baseline ({baseline_pred:.1f}/batch)")
ax.set_xlabel(f"Batch of {BATCH_SIZE} landings (sequential, not calendar months)")
ax.set_ylabel(f"{FOCUS_PART} replacements per batch")
ax.set_title(f"Baseline benchmark — MAE = {mae:.2f} units/batch of {BATCH_SIZE} landings")
ax.legend(fontsize=9)
fig.tight_layout()
fig.savefig(FIG / "03_baseline_forecast.png", dpi=160)
plt.close(fig)
batch_counts.to_csv(DOCS / "baseline_batch_demand.csv")

# ---------------------------------------------------------------------------
# ABC / XYZ dual-matrix classification (real rates, assumed annual landings)
# ---------------------------------------------------------------------------
ASSUMED_ANNUAL_LANDINGS = 2000  # flagged assumption — see Section 9

usage = []
for flag, name in PART_MAP.items():
    rate = df[flag].mean()
    cost = parts.loc[parts.part_id == flag, "unit_cost_inr"].iloc[0]
    annual_qty = rate * ASSUMED_ANNUAL_LANDINGS
    cv = batch_counts[name].std() / batch_counts[name].mean()
    usage.append({"part_name": name, "failure_rate": rate, "unit_cost_inr": cost,
                  "annual_qty": round(annual_qty, 1), "annual_value_inr": round(annual_qty * cost),
                  "demand_cv": cv})

abc_xyz = pd.DataFrame(usage).sort_values("annual_value_inr", ascending=False)
abc_xyz["cum_value_pct"] = abc_xyz["annual_value_inr"].cumsum() / abc_xyz["annual_value_inr"].sum() * 100
abc_xyz["abc_class"] = pd.cut(abc_xyz["cum_value_pct"], bins=[0, 80, 95, 100], labels=["A", "B", "C"])
abc_xyz["xyz_class"] = pd.cut(abc_xyz["demand_cv"], bins=[-0.01, 0.15, 0.30, 10], labels=["X", "Y", "Z"])
abc_xyz.to_csv(DOCS / "abc_xyz_classification.csv", index=False)

fig, ax = plt.subplots(figsize=(7.5, 5))
class_colors = {"A": NAVY, "B": TEAL, "C": GREY}
for _, r in abc_xyz.iterrows():
    ax.scatter(r["demand_cv"], r["annual_value_inr"] / 1e7, s=200,
               color=class_colors[r["abc_class"]], edgecolor="white", linewidth=1.2, zorder=3)
    ax.annotate(f"{r['part_name']}\n({r['abc_class']}{r['xyz_class']})",
                (r["demand_cv"], r["annual_value_inr"] / 1e7),
                textcoords="offset points", xytext=(10, 4), fontsize=9)
ax.set_xlabel("Demand coefficient of variation across batches  (X: stable → Z: erratic)")
ax.set_ylabel("Annual consumption value (₹ crore)")
ax.set_title("ABC/XYZ classification — real failure rates, assumed 2,000 landings/yr")
ax.set_xlim(left=0)
fig.tight_layout()
fig.savefig(FIG / "04_abc_xyz_matrix.png", dpi=160)
plt.close(fig)

# ---------------------------------------------------------------------------
# Apriori — real companion-part co-occurrence, mined from the 4 failure flags
# ---------------------------------------------------------------------------
basket_df = df[FLAGS].astype(bool)
basket_df.columns = [PART_MAP[c] for c in basket_df.columns]
freq_items = apriori(basket_df, min_support=0.15, use_colnames=True)
rules = association_rules(freq_items, metric="lift", min_threshold=1.05)
rules = rules[rules["antecedents"].apply(len) == 1]
rules = rules[rules["consequents"].apply(len) == 1]
rules = rules.sort_values("lift", ascending=False)
rules_out = rules[["antecedents", "consequents", "support", "confidence", "lift"]].copy()
rules_out["antecedents"] = rules_out["antecedents"].apply(lambda s: ", ".join(sorted(s)))
rules_out["consequents"] = rules_out["consequents"].apply(lambda s: ", ".join(sorted(s)))
rules_out.round(3).to_csv(DOCS / "apriori_rules.csv", index=False)

top_rules = rules_out.head(6).iloc[::-1]
fig, ax = plt.subplots(figsize=(9.0, 4.2))
labels = [f"{a} → {c}" for a, c in zip(top_rules["antecedents"], top_rules["consequents"])]
ax.barh(labels, top_rules["lift"], color=TEAL)
ax.set_xlabel("Lift"); ax.set_title("Real companion-part co-occurrence rules (Apriori)", fontsize=12)
fig.tight_layout()
fig.savefig(FIG / "05_apriori_rules.png", dpi=160)
plt.close(fig)

# ---------------------------------------------------------------------------
# Business case — AOG cost exposure & holding cost, in INR (unchanged formulas)
# ---------------------------------------------------------------------------
USD_TO_INR = 96.0
aog_cost_per_hr_usd = {"Low\n(narrowbody,\ndomestic)": 10_000, "Mid\n(narrowbody,\ntypical)": 45_000, "High\n(widebody,\npeak)": 150_000}
aog_hours_avoided = 18
focus_unit_cost_inr = float(parts.loc[parts.part_name == "Landing Gear Actuator", "unit_cost_inr"].iloc[0])

aog_rows = []
for label, usd_hr in aog_cost_per_hr_usd.items():
    inr_hr = usd_hr * USD_TO_INR
    exposure = inr_hr * aog_hours_avoided
    aog_rows.append({"scenario": label, "aog_cost_per_hr_inr": inr_hr, "exposure_per_event_inr": exposure})
aog_df = pd.DataFrame(aog_rows)
aog_df.to_csv(DOCS / "aog_cost_scenarios.csv", index=False)

holding_rate = 0.25
avg_stock_units = 4
holding_cost_annual_inr = focus_unit_cost_inr * avg_stock_units * holding_rate

fig, ax = plt.subplots(figsize=(8.5, 4.6))
ax.bar(aog_df["scenario"], aog_df["exposure_per_event_inr"] / 1e5, color=[GREY, TEAL, NAVY], width=0.55)
ax.axhline(holding_cost_annual_inr / 1e5, color=AMBER, linestyle="--", linewidth=1.4,
           label=f"Annual holding cost of 4 spare Landing Gear Actuators (₹{holding_cost_annual_inr/1e5:.1f} lakh)")
ax.set_ylabel("₹ lakh")
ax.set_title("Per-event AOG cost exposure vs. annual holding cost — Landing Gear Actuator", fontsize=12)
ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.1f"))
ax.tick_params(axis="x", labelsize=9)
ax.legend(fontsize=8, loc="upper left")
fig.tight_layout()
fig.savefig(FIG / "06_business_case.png", dpi=160)
plt.close(fig)

# ---------------------------------------------------------------------------
print("Wrote figures to", FIG, "and tables to", DOCS)
print(f"\nBaseline: constant {baseline_pred:.1f}/batch, MAE = {mae:.2f} units per {BATCH_SIZE}-landing batch")
print(f"Holding cost (4 units, 25%/yr): INR {holding_cost_annual_inr:,.0f}")
print()
print(abc_xyz[["part_name", "failure_rate", "abc_class", "xyz_class", "annual_value_inr"]].to_string(index=False))
print()
print(f"Real correlation with brake_degradation: braking_force={df[['braking_force','brake_degradation']].corr().iloc[0,1]:.3f}, "
      f"load={df[['load_during_landing','brake_degradation']].corr().iloc[0,1]:.3f}, "
      f"landing_cycles={df[['landing_cycles','brake_degradation']].corr().iloc[0,1]:.3f}")
