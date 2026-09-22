import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyArrowPatch
from pathlib import Path

FIG = Path(__file__).resolve().parent.parent / "reports" / "figures"
NAVY, TEAL, AMBER, GREY, LIGHT = "#2f5872", "#3f8c9e", "#d98c3a", "#8a94a3", "#eef2f5"

fig, ax = plt.subplots(figsize=(11, 6.4))
ax.set_xlim(0, 11); ax.set_ylim(0, 6.4); ax.axis("off")

def box(x, y, w, h, text, color=NAVY, fontsize=9.5, fontcolor="white"):
    r = mpatches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.08",
                                 linewidth=0, facecolor=color)
    ax.add_patch(r)
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
            fontsize=fontsize, color=fontcolor, wrap=True, linespacing=1.3)
    return (x, y, w, h)

def arrow(b1, b2, side1="right", side2="left", color="#5a6472"):
    x1, y1, w1, h1 = b1; x2, y2, w2, h2 = b2
    pts = {"right": (x1 + w1, y1 + h1 / 2), "left": (x2, y2 + h2 / 2),
           "bottom": (x1 + w1 / 2, y1), "top": (x2 + w2 / 2, y2 + h2)}
    p1 = pts[side1]; p2 = pts[side2]
    ax.add_patch(FancyArrowPatch(p1, p2, arrowstyle="-|>", mutation_scale=14,
                                  color=color, linewidth=1.4))

# Row 1: Data sources
d1 = box(0.2, 5.0, 2.1, 1.1, "Airbus Landing Gear\nsensor data (Kaggle)", TEAL)
d2 = box(0.2, 3.6, 2.1, 1.1, "Maintenance teardown\nlogs", TEAL)
d3 = box(0.2, 2.2, 2.1, 1.1, "Flight-cycle & fleet\nconfiguration data", TEAL)

# Preprocessing
pp = box(2.9, 3.6, 2.0, 1.3, "Preprocessing &\nfeature engineering\n(wear index, env. flags)", NAVY)
arrow(d1, pp, "right", "left")
arrow(d2, pp, "right", "left")
arrow(d3, pp, "right", "left")

# Analytics core (3 parallel engines)
abc = box(5.5, 4.9, 2.1, 1.1, "ABC/XYZ dual-matrix\nclassification", NAVY)
ml = box(5.5, 3.55, 2.1, 1.1, "LightGBM demand\nforecast model", NAVY)
mba = box(5.5, 2.2, 2.1, 1.1, "Apriori market-basket\n(companion parts)", NAVY)
for b in (abc, ml, mba):
    arrow(pp, b, "right", "left")

# Business layer
biz = box(8.15, 3.55, 2.05, 1.4, "Cost & reorder engine\n(AOG cost, holding cost,\nROP, batch size — ₹)", AMBER, fontcolor="#332200")
arrow(abc, biz, "right", "left")
arrow(ml, biz, "right", "left")
arrow(mba, biz, "right", "left")

# Dashboard
dash = box(8.15, 0.5, 2.05, 1.1, "Supplier-facing\ninteractive dashboard", GREY, fontcolor="#22262b")
arrow(biz, dash, "bottom", "top")

ax.text(0.2, 0.35, "Excluded from scope: live telemetry / weather API streaming (per Section 4, Scope of Work)",
        fontsize=8.5, color="#6b7482", style="italic")

ax.text(0.1, 6.15, "System Architecture — Predictive Spare-Parts Demand Forecasting Pipeline",
        fontsize=13, fontweight="bold", color="#1f2d3a")

fig.tight_layout()
fig.savefig(FIG / "00_architecture.png", dpi=170)
print("Saved architecture diagram")
