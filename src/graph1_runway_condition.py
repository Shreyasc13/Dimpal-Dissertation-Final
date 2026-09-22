"""
Standalone: recreates Graph 1 (runway condition vs landing-load quintile)
on its own, so you can run it, tweak it, and see the window live.
"""
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
df = pd.read_csv(ROOT / "data" / "processed" / "landing_events.csv")

TARGET_FLAG = "shock_absorber_failure"  # Landing Gear Actuator
TEAL, NAVY, AMBER = "#3f8c9e", "#2f5872", "#d98c3a"

fig, axes = plt.subplots(1, 2, figsize=(11, 4.4))

# --- Left panel: by runway condition ---
rc_rates = df.groupby("runway_condition")[TARGET_FLAG].mean().reindex(["dry", "wet", "snowy"])
axes[0].bar(rc_rates.index, rc_rates.values * 100, color=[TEAL, "#5a9fb0", NAVY], width=0.55)
axes[0].set_ylim(50, 70)
axes[0].set_ylabel("Landing Gear Actuator failure rate (%)")
axes[0].set_title("By runway condition\n(barely moves)", fontsize=11)

# --- Right panel: by landing weight, lightest to heaviest ---
LOAD_LABELS = ["Lightest\n20%", "2nd\nlightest", "Middle\n20%", "2nd\nheaviest", "Heaviest\n20%"]
df["load_q"] = pd.qcut(df["load_during_landing"], 5, labels=LOAD_LABELS)
ld_rates = df.groupby("load_q", observed=True)[TARGET_FLAG].mean().reindex(LOAD_LABELS)
axes[1].bar(ld_rates.index.astype(str), ld_rates.values * 100, color=AMBER, width=0.55)
axes[1].set_ylim(0, 100)
axes[1].set_ylabel("Landing Gear Actuator failure rate (%)")
axes[1].set_title("By landing weight, lightest to heaviest\n(strong upward trend)", fontsize=11)

fig.suptitle("What actually drives Landing Gear Actuator failure: landing load, not weather",
             fontsize=13, fontweight="bold", y=1.03)
fig.tight_layout()

plt.show()  # <-- opens a live window on your screen instead of just saving a file
