"""
Standalone: recreates Graph 4 (baseline benchmark) on its own.
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
df = pd.read_csv(ROOT / "data" / "processed" / "landing_events.csv")
parts = pd.read_csv(ROOT / "data" / "processed" / "parts_master.csv")

PART_MAP = dict(zip(parts["part_id"], parts["part_name"]))
FLAGS = list(PART_MAP.keys())
NAVY, AMBER = "#2f5872", "#d98c3a"

# --- Split the 10,000 landings into 50 groups of 200, in file order ---
BATCH_SIZE = 200
df["batch"] = np.arange(len(df)) // BATCH_SIZE
batch_counts = df.groupby("batch")[FLAGS].sum()
batch_counts.columns = [PART_MAP[c] for c in batch_counts.columns]

# --- The "lazy guess": just the average count per batch ---
FOCUS_PART = "Landing Gear Actuator"
baseline_pred = batch_counts[FOCUS_PART].mean()
mae = (batch_counts[FOCUS_PART] - baseline_pred).abs().mean()
print(f"Average per batch (the flat guess): {baseline_pred:.1f}")
print(f"MAE (how wrong the flat guess is on average): {mae:.2f}")

fig, ax = plt.subplots(figsize=(7.5, 4.2))
ax.plot(batch_counts.index, batch_counts[FOCUS_PART], marker="o", markersize=3, color=NAVY, label="Actual replacements per batch")
ax.axhline(baseline_pred, color=AMBER, linestyle="--", linewidth=1.4, label=f"Constant baseline ({baseline_pred:.1f}/batch)")
ax.set_xlabel(f"Batch of {BATCH_SIZE} landings (sequential, not calendar months)")
ax.set_ylabel(f"{FOCUS_PART} replacements per batch")
ax.set_title(f"Baseline benchmark — MAE = {mae:.2f} units/batch of {BATCH_SIZE} landings")
ax.legend(fontsize=9)
fig.tight_layout()

plt.show()  # opens a live window
