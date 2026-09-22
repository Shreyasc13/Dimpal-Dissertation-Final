# Data setup

I can't log into Kaggle to pull these files for you, so grab them manually (2-minute job) and drop them in this folder.

## 1. Primary dataset — Airbus Landing Gear Predictive Maintenance
https://www.kaggle.com/datasets/justineskind/landing-gear-predictive-maintenance
- Click "Download" (Kaggle account required, free).
- Unzip into `data/raw/landing_gear/`.

## 2. Benchmark dataset — NASA C-MAPSS Turbofan Engine Degradation
https://www.kaggle.com/datasets/behrad3d/nasa-cmaps
- Download and unzip into `data/raw/cmapss/`.
- We're only using this one to benchmark modeling approach/methodology (see literature review), not as primary training data.

Once both are in place, tell me and I'll kick off the EDA notebook.

### Alternative: Kaggle CLI
If you'd rather script it:
```
pip install kaggle
# place your kaggle.json API token (from kaggle.com/settings) at ~/.kaggle/kaggle.json
kaggle datasets download -d justineskind/landing-gear-predictive-maintenance -p data/raw/landing_gear --unzip
kaggle datasets download -d behrad3d/nasa-cmaps -p data/raw/cmapss --unzip
```
