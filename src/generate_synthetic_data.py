"""
Generates a structurally-representative stand-in for the Kaggle "Landing Gear
Predictive Maintenance" dataset (justineskind/landing-gear-predictive-maintenance),
which records brake temperature/pressure/wheel-speed for 8 wheels across the last
100 seconds of ~109 landings for an Airbus fleet.

This is a PLACEHOLDER for the midterm checkpoint, built while the real Kaggle
CSV is being downloaded. Schema mirrors the real dataset so this script's output
can be swapped for the real file with no changes downstream (see data/raw/DATA_SETUP.md).
"""
import numpy as np
import pandas as pd
from pathlib import Path

RNG = np.random.default_rng(42)
OUT = Path(__file__).resolve().parent.parent / "data" / "processed"
OUT.mkdir(parents=True, exist_ok=True)

N_LANDINGS = 109
N_WHEELS = 8
TIMESTEPS = 100
FLEET = [f"VT-A{i:02d}" for i in range(1, 7)]  # 6-aircraft simulated fleet

# ---------------------------------------------------------------------------
# 1. Raw per-landing, per-wheel sensor time series (brake temp/pressure/speed)
# ---------------------------------------------------------------------------
rows = []
landing_dates = pd.date_range("2024-06-01", periods=N_LANDINGS, freq="3D")

env_flags = RNG.choice(["cold_snow", "temperate"], size=N_LANDINGS, p=[0.3, 0.7])
tails = RNG.choice(FLEET, size=N_LANDINGS)
cum_cycles = {t: 0 for t in FLEET}

landing_summary = []

for i in range(N_LANDINGS):
    tail = tails[i]
    cum_cycles[tail] += 1
    env = env_flags[i]
    severity = 1.35 if env == "cold_snow" else 1.0  # harsher braking in cold/snow

    for wheel in range(1, N_WHEELS + 1):
        t = np.arange(TIMESTEPS)
        base_temp = 80 + 220 * np.exp(-t / 28) * severity
        noise = RNG.normal(0, 6, TIMESTEPS)
        brake_temp = base_temp + noise

        base_pressure = 2800 * np.exp(-t / 20) * severity + 150
        brake_pressure = base_pressure + RNG.normal(0, 40, TIMESTEPS)

        wheel_speed = np.maximum(0, 145 - 1.6 * t + RNG.normal(0, 3, TIMESTEPS))

        for step in range(TIMESTEPS):
            rows.append((i + 1, landing_dates[i], tail, env, wheel,
                         brake_temp[step], brake_pressure[step], wheel_speed[step]))

    peak_temp = np.max([r[5] for r in rows if r[0] == i + 1])
    landing_summary.append({
        "landing_id": i + 1, "date": landing_dates[i], "tail_number": tail,
        "environment": env, "flight_cycle": cum_cycles[tail],
        "peak_brake_temp_c": peak_temp,
    })

sensor_df = pd.DataFrame(rows, columns=[
    "landing_id", "date", "tail_number", "environment", "wheel_id",
    "brake_temp_c", "brake_pressure_psi", "wheel_speed_kmh"
])
sensor_df.to_csv(OUT / "landing_gear_sensor_timeseries.csv", index=False)

landing_df = pd.DataFrame(landing_summary)

# ---------------------------------------------------------------------------
# 2. Derived per-landing wear index -> cumulative wear -> replacement events
#    (label engineering: raw dataset has no failure labels, so we derive a
#    physically-motivated wear proxy from peak brake temperature)
# ---------------------------------------------------------------------------
landing_df["wear_increment"] = np.clip((landing_df["peak_brake_temp_c"] - 150) / 40, 0.2, None)
landing_df = landing_df.sort_values(["tail_number", "flight_cycle"])
landing_df["cum_wear"] = landing_df.groupby("tail_number")["wear_increment"].cumsum()
landing_df.to_csv(OUT / "landing_summary_features.csv", index=False)

# ---------------------------------------------------------------------------
# 3. Parts master (for ABC/XYZ classification) — landing-gear assembly + its
#    companion parts, in INR, priced off typical aerospace component bands
# ---------------------------------------------------------------------------
USD_TO_INR = 96.0
parts_master = pd.DataFrame([
    {"part_id": "LGA-001", "part_name": "Landing Gear Actuator", "unit_cost_usd": 45000},
    {"part_id": "BRK-002", "part_name": "Brake Assembly", "unit_cost_usd": 18000},
    {"part_id": "WHL-003", "part_name": "Wheel Unit", "unit_cost_usd": 6000},
    {"part_id": "HYD-004", "part_name": "Hydraulic Line", "unit_cost_usd": 2500},
    {"part_id": "SNS-005", "part_name": "Sensor Unit", "unit_cost_usd": 300},
    {"part_id": "SEL-006", "part_name": "Seal Kit", "unit_cost_usd": 150},
    {"part_id": "BLT-007", "part_name": "Structural Bolt Set", "unit_cost_usd": 80},
])
parts_master["unit_cost_inr"] = (parts_master["unit_cost_usd"] * USD_TO_INR).round(0)
parts_master.to_csv(OUT / "parts_master.csv", index=False)

# ---------------------------------------------------------------------------
# 4. Maintenance teardown log: a replacement event fires when cum_wear crosses
#    a threshold; companion parts co-replaced with set probabilities (feeds
#    the Apriori / market-basket analysis)
# ---------------------------------------------------------------------------
THRESHOLD = 6.0
events = []
event_id = 1
for tail, g in landing_df.groupby("tail_number"):
    g = g.sort_values("flight_cycle")
    next_threshold = THRESHOLD
    for _, r in g.iterrows():
        if r["cum_wear"] >= next_threshold:
            basket = ["Brake Assembly"]
            if RNG.random() < 0.72:
                basket.append("Seal Kit")
            if RNG.random() < 0.58:
                basket.append("Structural Bolt Set")
            if RNG.random() < 0.22:
                basket.append("Wheel Unit")
            if RNG.random() < 0.07:
                basket.append("Landing Gear Actuator")
            events.append({
                "event_id": event_id, "date": r["date"], "tail_number": tail,
                "environment": r["environment"], "flight_cycle": r["flight_cycle"],
                "parts_replaced": ";".join(basket),
            })
            event_id += 1
            next_threshold += THRESHOLD

maintenance_log = pd.DataFrame(events)
maintenance_log.to_csv(OUT / "maintenance_teardown_log.csv", index=False)

print(f"landings: {len(landing_df)} | sensor rows: {len(sensor_df)} | "
      f"maintenance events: {len(maintenance_log)}")
print("Saved to", OUT)
