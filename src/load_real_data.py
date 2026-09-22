"""
Loads the real Kaggle dataset (landing_gear_maintenance_simulated_data.xlsx —
10,000 landing records with operating conditions and 4 real failure/wear
flags) and maps it onto the project's parts basket.

This REPLACES generate_synthetic_data.py, which was a placeholder built
before the real file was downloaded. Kept generate_synthetic_data.py in
the repo for history, but it is no longer used downstream.
"""
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw" / "landing_gear" / "landing_gear_maintenance_simulated_data.xlsx"
OUT = ROOT / "data" / "processed"
OUT.mkdir(parents=True, exist_ok=True)

# Each failure/wear flag maps to one physical part in the parts basket.
# tire_wear -> Wheel Unit, shock_absorber_failure -> Landing Gear Actuator
# (shock absorbers are a subcomponent of the landing-gear strut/actuator).
PART_MAP = {
    "brake_degradation": "Brake Assembly",
    "shock_absorber_failure": "Landing Gear Actuator",
    "tire_wear": "Wheel Unit",
    "hydraulic_system_failure": "Hydraulic Line",
}

USD_TO_INR = 96.0
UNIT_COST_USD = {
    "Landing Gear Actuator": 45000,
    "Brake Assembly": 18000,
    "Wheel Unit": 6000,
    "Hydraulic Line": 2500,
}

df = pd.read_excel(RAW)
df.to_csv(OUT / "landing_events.csv", index=False)

parts_master = pd.DataFrame([
    {"part_id": flag, "part_name": name, "unit_cost_usd": UNIT_COST_USD[name],
     "unit_cost_inr": round(UNIT_COST_USD[name] * USD_TO_INR)}
    for flag, name in PART_MAP.items()
])
parts_master.to_csv(OUT / "parts_master.csv", index=False)

print(f"Loaded {len(df)} real landing records, {df.shape[1]} columns")
print("Columns:", list(df.columns))
print("\nFailure/wear rates:")
for flag, name in PART_MAP.items():
    print(f"  {name:24s} ({flag}): {df[flag].mean()*100:.1f}%")
