"""
Standalone: recreates Graph 2 (correlation heatmap) on its own.
"""
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
df = pd.read_csv(ROOT / "data" / "processed" / "landing_events.csv")
parts = pd.read_csv(ROOT / "data" / "processed" / "parts_master.csv")

PART_MAP = dict(zip(parts["part_id"], parts["part_name"]))
FLAGS = list(PART_MAP.keys())
NUM_FEATURES = ["landing_cycles", "load_during_landing", "taxiing_duration",
                 "speed_during_landing", "braking_force", "tire_pressure", "hydraulic_pressure"]

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

plt.show()  # opens a live window
