import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyArrowPatch
from pathlib import Path

FIG = Path(__file__).resolve().parent.parent / "reports" / "figures"
NAVY, TEAL, AMBER, GREY = "#2f5872", "#3f8c9e", "#d98c3a", "#8a94a3"

fig, ax = plt.subplots(figsize=(13, 5.6))
ax.set_xlim(0, 13); ax.set_ylim(0, 5.6); ax.axis("off")

def box(x, y, w, h, text, color=NAVY, fontsize=9.3, fontcolor="white"):
    r = mpatches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.08",
                                 linewidth=0, facecolor=color)
    ax.add_patch(r)
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
            fontsize=fontsize, color=fontcolor, wrap=True, linespacing=1.3)
    return (x, y, w, h)

def anchor(b, side):
    x, y, w, h = b
    return {"right": (x + w, y + h / 2), "left": (x, y + h / 2),
            "bottom": (x + w / 2, y), "top": (x + w / 2, y + h)}[side]

def arrow(b1, b2, side1="right", side2="left", color="#5a6472", dashed=False):
    p1, p2 = anchor(b1, side1), anchor(b2, side2)
    ax.add_patch(FancyArrowPatch(p1, p2, arrowstyle="-|>", mutation_scale=13,
                                  color=color, linewidth=1.3,
                                  linestyle=(0, (5, 3)) if dashed else "solid"))

# --- Primary path (solid): dataset -> preprocessing -> classification -> forecast -> cost -> dashboard ---
d1 = box(0.15, 3.55, 1.75, 1.5, "Landing-gear\nmaintenance dataset\n(Kaggle, 10,000\nreal landings)", TEAL)
pp = box(2.15, 3.65, 1.75, 1.3, "Preprocessing &\nfeature engineering\n(flag → part mapping,\nseverity features)", NAVY)
cls = box(4.15, 3.65, 1.85, 1.3, "Value/Volatility\nClassification\n(picks the one part\nworth forecasting)", NAVY)
fc = box(6.25, 3.65, 1.75, 1.3, "Demand Forecast\nModel\n(LightGBM)", NAVY)
cost = box(8.25, 3.65, 1.95, 1.3, "Cost & Reorder\nEngine\n(AOG cost, holding\ncost, ROP, batch size)", AMBER, fontcolor="#332200")
dash = box(10.5, 2.2, 2.1, 1.3, "Supplier\nInteractive\nDashboard", GREY, fontcolor="#22262b")

for a, b in [(d1, pp), (pp, cls), (cls, fc), (fc, cost)]:
    arrow(a, b, "right", "left")
arrow(cost, dash, "right", "left")

# --- Optional branch (dashed): preprocessing -> companion-parts mining -> dashboard ---
mba = box(4.15, 1.1, 1.85, 1.3, "Companion-Parts\nMining (Apriori)\nmodule", NAVY)
arrow(pp, mba, "bottom", "top", dashed=True)
arrow(mba, dash, "right", "left", dashed=True)

ax.text(4.2, 0.75, "Optional: shown only if a supplier chooses to see bundling suggestions",
        fontsize=8.3, color="#6b7482", style="italic")

ax.text(0.15, 5.35, "System Architecture: Predictive Spare-Parts Demand Forecasting Pipeline",
        fontsize=13, fontweight="bold", color="#1f2d3a")

ax.text(0.15, 0.2, "Excluded from scope: live telemetry / weather API streaming",
        fontsize=8.3, color="#6b7482", style="italic")

fig.tight_layout()
fig.savefig(FIG / "00_architecture.png", dpi=300)
print("Saved architecture diagram")
