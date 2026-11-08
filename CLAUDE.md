# Project: Demand Forecasting In Inventory Management

Dissertation project — **Dimpal Shetty**, BITS Pilani M.Tech Software Systems (2024MT13052), course **S1-26_SSZG628T**, carried out at **Airbus India Pvt Ltd Bangalore** under supervisor **Saurabh Mahajan** (additional examiner: Karthik Mahadevan).

This file exists so a Claude Code session on a different machine can pick up this project with full context. Read this before doing anything else in this repo.

## Communication style — read this first

- User wants everything explained in **very simple, plain English** — no "AI language," no fancy/academic words, no jargon left undefined. Expect to re-explain the same concept multiple times in different ways; that's normal for this user, not a sign something's wrong.
- **Always verify numbers/facts from the actual code or data before stating them.** Several past mistakes in this project came from confidently stating things from memory that turned out wrong (see "Known past errors" below). Run the actual script or grep the actual file rather than recalling a number.
- User explicitly wants assumptions, placeholders, and anything invented flagged proactively, before the examiner/supervisor would catch it. Don't hide weak points — own them.
- User frequently asks for help rehearsing verbal answers for mentor meetings / viva. These should be plain spoken scripts, not technical write-ups.
- Be careful not to overclaim progress. If something hasn't actually been built/run, say so plainly rather than describing it as "informal" or "preliminary" progress that doesn't really exist. (See the LightGBM correction in project history — I incorrectly implied an informal LightGBM test existed; it didn't, only the baseline did.)

## Current status (as of 2026-11-08)

**Done:** Phases 1–4 — real-data pipeline, EDA, Value/Volatility (ABC/XYZ) classification, Apriori companion-parts mining, business/cost-benefit case, midterm report, architecture diagram, viva presentation decks (both a Claude Artifact Slides deck and a Google-Slides-ready .pptx).

### ⚠️ CRITICAL FINDING (2026-11-08, Phase 5): the dataset is rule-generated, not real landings
The Kaggle file is literally named `..._simulated_data.xlsx`. Each of the 4 failure flags is an **exact 2-condition rule**, matching 10,000/10,000 rows (verified with a depth-2 decision tree):
| Flag (part) | Exact rule for failure = 1 |
|---|---|
| shock_absorber_failure (Actuator) | load_during_landing > 70 OR landing_cycles > 401 |
| tire_wear (Wheel Unit) | braking_force > 40 OR landing_cycles > 300 |
| brake_degradation (Brake Assembly) | braking_force > 35 OR landing_cycles > 351.5 |
| hydraulic_system_failure (Hydraulic Line) | hydraulic_pressure < 2800 OR landing_cycles > 450.5 |

Consequences, which must be disclosed and never hidden:
- runway_condition/weather is in **no** rule. So "severity beats weather" is a property of how the simulator was written, not a real-world finding. The per-runway robustness check is valid but only proves the simulator ignores weather.
- The midterm report says "10,000 real aircraft landing(s)" and the deck says "real data". That's an **overclaim**: it's a real public file of *simulated* data.
- Phase 5 models are near-perfect because they rediscover the rule (AUC 1.000). The best possible error is 0, because there's no randomness left.
- **DECISION (user, 2026-11-08): KEEP this dataset. Do not suggest switching datasets again.** Frame it honestly in the final report: it's simulated data, the contribution is the *method/pipeline*, and real airline data is needed to confirm the numbers. Replace "real landings/real data" wording with "simulated". Add a Limitations paragraph. Supervisor should be told; a spoken script was offered.

### Phase 5 results (2026-11-08) — `src/phase5_lightgbm.py`
Per-landing probability model on 8 conditions (other failure flags NOT used as inputs), summed per 200-landing batch. 5-fold test over batches (each batch tested by a model that never saw it), with inner-CV tuning on training batches only.
| Method | Batch MAE |
|---|---|
| Original baseline (all-batch average) | 5.52 |
| Fair baseline (training-batch average only) | 6.18 |
| Random Forest (tuned) | **0.10** |
| LightGBM (tuned; most-chosen: num_leaves 7, lr 0.03, 300 trees) | **0.30** |
LightGBM feature importance (gain): load 99.1%, landing_cycles 0.7%, everything else ~0, runway 0.0%. **Random Forest beat LightGBM here.** The sharp threshold suits fully-grown trees, and LightGBM's small learning rate gives softer probabilities near the cutoff. Report this honestly; both are ~0.1–0.3 units per 200 landings, so the difference has no practical effect.
Env note: **lightgbm 4.7.0 crashes** (access violation) on this machine with Python 3.12.0, so it's pinned to **lightgbm==4.6.0**. numpy must stay ≥2.3.5 for mlxtend.
Outputs: `reports/docs/phase5_*.csv`, `reports/figures/07–09_phase5_*.png`.

### Phase 6 results (2026-11-08) — `src/phase6_reorder_engine.py` (run after phase5)
Each 200-landing batch = one planning period; the shelf is topped up to target = forecast + z × (typical error). Typical error is measured on the OTHER folds only. z comes from the newsvendor ratio: short cost (1 AOG event) ÷ (short cost + holding cost of 1 unit for 1 batch = ₹1,08,000). That gives target service 99.38% / 99.86% / 99.96% (z 2.50 / 2.99 / 3.34) for Low/Mid/High.
| Mid AOG scenario | Avg safety buffer | Batches short | Cost/yr |
|---|---|---|---|
| Constant baseline | 22.8 units | 0 | ₹2.46 cr |
| LightGBM | 2.0 units | 0 | ₹0.21 cr |
| Random Forest | 1.0 unit | 0 | ₹0.10 cr |
Low: 2.05 / 0.20 / 0.10 cr. High: 2.74 / 0.22 / 0.11 cr. **No method ran short in any of the 50 batches**, so all the savings come from holding ~20 fewer spare units for the same protection: about ₹1.85–2.5 cr/yr with LightGBM. Honest caveat: 50 batches is too few to test rare stockouts properly.
Assumptions to disclose: 2,000 landings/yr (batch = 0.1 yr); orders arrive before the batch starts; each unit short = one 18-h AOG event; the forecast uses the landing's own conditions (in real use, these would come from flight plans/known cycle counts).
Scale note: forecast demand is ~119 actuators per 200 landings (because the simulated failure rate is 60%). That's unrealistically high for real aircraft, and it doesn't sit well with the midterm's "4 spare units" holding example. Flag it as a dataset artefact.
**Order size (EOQ)**, added to fulfil the midterm's "ROP/batch-size formulas" promise: EOQ = √(2 × yearly demand × order cost ÷ holding cost per unit per year of ₹10,80,000). Yearly demand is ~1,194 units for every method, so EOQ is the same whichever forecast is used; the model's value is in the safety buffer, not the order size. Order cost is an **invented assumption** (main ₹50,000):
| Order cost | EOQ | Orders/yr | Orders per batch |
|---|---|---|---|
| ₹25,000 | 7 | 171 | 17 |
| **₹50,000** | **11** | **109** | **11** |
| ₹1,00,000 | 15 | 80 | 8 |
| ₹2,00,000 | 21 | 57 | 6 |
Outputs: `reports/docs/phase6_*.csv` (incl. `phase6_order_size_eoq.csv`), `reports/figures/10_phase6_total_cost.png`, `11_phase6_stock_levels.png`.
**Status: Phases 5, 6 and 7-dashboard DONE (2026-11-08). Final report FIRST DRAFT written (2026-11-08)** as LaTeX at `reports/final_report/main.tex`, following the BITS WILP report guidelines (user was asked to write it in LaTeX). It has 10 chapters plus appendices A–C, references and a glossary with page refs. Upload `final_report_overleaf.zip` to Overleaf (pdfLaTeX). **Compiles cleanly locally (2026-11-08) with MiKTeX** (user installed it at `%LOCALAPPDATA%\Programs\MiKTeX`, auto-install of packages on): run `pdflatex -interaction=nonstopmode main.tex` twice in `reports/final_report/`. Output is `main.pdf`, 45 pages, about 1.7 MB. **All placeholders filled (2026-11-08) from the user's answers:** submitted November 2026 / 10 Nov 2026; station "Bengaluru, Karnataka"; start **08 Aug 2026** (regularised to match the midterm plan); duration **13 weeks**; signature date 09-11-2026; faculty mentor **Ashish Narang**; Saurabh Mahajan = **"HO of Architecture"** (user's exact wording; keep it, don't expand it); Karthik Mahadevan = Digital Sourcing Lead; manager PhaniKiran Vemagal. Acknowledgements follow the BITS order. There is no head of org (per the user), so the order is: supervisor Saurabh → additional examiner Karthik → faculty mentor Ashish → manager PhaniKiran (as "other persons"). No family line. Dataset citation: Eskind, J., "Landing Gear Predictive Maintenance", Kaggle, v1, CC0, 2024, accessed 10 Sep 2026 (checked via Kaggle's public API). Section 1.7 "Organisation of the report" was removed at the user's request. **More user edits (2026-11-08), don't undo them:** removed section "Changes since the midterm report"; removed "Simulated data" from the Limitations chapter (the user will explain it verbally; it's still disclosed in Ch 3.5, Ch 6.6, the abstract and the conclusions); removed the appendix "Reproducing the Results" (appendices are now A = settings per fold, B = batch forecasts); problem statement is plain text, not italic; no "(Supervisor)/(Additional Examiner)" after names on the abstract sheet; short bracket-free titles in the List of Figures/Tables (`\caption[short]{long}`); no paragraph indents (`\parindent 0`, `\parskip 6pt`); `includefoot` so page numbers sit inside the 1" margin. Now 50 pages. Uses "Rs." via `\INR` macro. The midterm wording fixes are applied in it (simulated, Prophet/LSTM, softened "far better", A/X, heatmap caption).

### ▶ RESUME HERE (session paused 2026-11-08 evening — now superseded by Phase 5/6 sections above)
- **Dataset:** downloaded again and placed at `data/raw/landing_gear/landing_gear_maintenance_simulated_data.xlsx`. Checked on 2026-11-08: 10,000×12, no missing values. Failure rates, runway rates, per-runway correlations (0.814/0.823/0.827) and baseline (mean 119.44, MAE 5.52) all match the report exactly.
- **Python:** the old 32-bit Python 3.8 can't install mlxtend/scipy or LightGBM, so don't use it. User installed **64-bit Python 3.12** at `C:\Users\Lenovo\AppData\Local\Programs\Python\Python312\python.exe`. The project `.venv` was rebuilt on it.
- **Install was interrupted:** `.venv` has pandas, openpyxl, matplotlib, scikit-learn. **Still missing: mlxtend, lightgbm.** The download was very slow (over 10 min). Finish with: `.\.venv\Scripts\python.exe -m pip install mlxtend lightgbm`, then check the imports.
- **Then:** run `src/load_real_data.py`, then `src/analysis_pipeline.py`, and confirm the outputs match `reports/docs/*.csv`. Then start **Phase 5**.
- **Phase 5 plan proposed to user (awaiting their OK):** train LightGBM on all 10,000 individual landings to predict each landing's actuator-failure probability. Sum the probabilities per 200-landing batch to get "units per batch" and compare its MAE against the 5.52 baseline, plus Random Forest (the report's Plan of Work promises "LightGBM vs. baseline/Random Forest"). Reason: there are only 50 batches, which is too few rows to train a model on directly.
- **Timeline:** the report's Plan of Work had Phase 7 finishing 2026-11-08, but Phases 5–7 haven't started. Remind the user to agree a new timeline with the supervisor.
- **Pending wording fixes (user not yet asked to apply them):**
  - Deck slide 7 says "Prophet/Random Trees"; it should be Prophet/LSTM.
  - Deck slide 4 says Olmo & Domingo is "modified for aviation", but it's already aerospace.
  - Soften "far better than flight cycles" (actuator: load 0.82 vs cycles 0.72).
  - Report Figure 3 caption overclaims "every part".
  - Report has broken text: "Class Value/Volatility" should be "Class A/X", stray "5.", "Section 15" reference (only 13 sections), "detailed in chiefly", missing Figure 6, "Supply Interactive" typo.
  - Kaggle link for the citation is in `data/raw/DATA_SETUP.md` (justineskind/landing-gear-predictive-maintenance); confirm the title and author.

**Not started yet:**
- **Phase 5 — LightGBM model training & tuning.** Nothing trained yet. Only the baseline (constant-average predictor, MAE 5.52) exists. This is the most important next technical step.
- **Phase 6 — Reorder-point engine**, validated against the AOG cost model (turn the forecast into an actual stock/reorder decision).
- ~~Phase 5, Phase 6, Phase 7 dashboard~~ — DONE 2026-11-08, see sections above. **Still to do: final dissertation writeup.**

**Open items needing the user's decision / input:**
- `reports/2024_MT_13052_Midterm_Dissertation.docx` — the user's manually-renamed/edited copy of the report has some content that looks accidentally deleted (Limitations section, Scope section, some Implementation Details table rows, the Apriori chart/Figure 6, broken grammar from stripped em-dashes) mixed with genuine intentional edits (reformatted cover, signature block moved, List of Figures/Tables removed). User was asked whether to restore the missing parts and never answered — **do not silently "fix" this file; ask first.**
- Exact Kaggle dataset citation (title/author/listing link) — still unresolved, report has `[Dataset citation pending]`.
- Real fleet-utilisation figure — business case currently assumes 2,000 landings/year, flagged as a placeholder throughout.
- Git remote: `origin` = https://github.com/Shreyasc13/Dimpal-Dissertation-Final.git (branch `master`).

## The dataset — ground truth, verified against actual files

Real Kaggle dataset: `data/raw/landing_gear/landing_gear_maintenance_simulated_data.xlsx` — 10,000 rows, 12 columns, no dates, no aircraft IDs.

**8 operating-condition columns (raw, unmodified):** `landing_cycles`, `load_during_landing`, `taxiing_duration`, `speed_during_landing`, `braking_force`, `tire_pressure`, `hydraulic_pressure`, `runway_condition`.

**4 binary failure/wear flags (raw, unmodified), mapped to parts (mapping is OUR interpretive choice, not in the raw file):**
| Raw column | Mapped part name | Real failure rate |
|---|---|---|
| `brake_degradation` | Brake Assembly | 95.3% |
| `shock_absorber_failure` | Landing Gear Actuator | 59.7% |
| `tire_wear` | Wheel Unit | 81.7% |
| `hydraulic_system_failure` | Hydraulic Line | 24.5% |

These don't sum to 100% because each landing gets 4 independent yes/no checks — one landing can trigger multiple failures at once (verified: e.g. 5,689 landings have both actuator AND wheel-unit failures together).

**Invented/assumed values (not in raw data — always disclose as assumptions):**
- Unit costs: Landing Gear Actuator ₹43,20,000 ($45,000), Brake Assembly ₹17,28,000 ($18,000), Wheel Unit ₹5,76,000 ($6,000), Hydraulic Line ₹2,40,000 ($2,500). USD→INR = 96.0.
- Assumed fleet utilisation: 2,000 landings/year.
- "Batch of 200 landings" = an artificial stand-in for a time period (no real dates exist), used consistently everywhere a "period" is needed.

## Key verified results (recompute via scripts below if in doubt — don't trust memory)

- **Baseline:** constant-average predictor over 50 batches of 200 landings → average 119.44/batch, MAE = **5.52** units/batch. This is the number Phase 5's LightGBM model needs to beat.
- **ABC/XYZ (Value/Volatility) classification:**
  | Part | Failure rate | Unit cost (₹) | Annual value | Demand CV | Class |
  |---|---|---|---|---|---|
  | Landing Gear Actuator | 59.7% | 43,20,000 | ₹516.0cr | 0.06 | A·X |
  | Brake Assembly | 95.3% | 17,28,000 | ₹329.3cr | 0.01 | B·X |
  | Wheel Unit | 81.7% | 5,76,000 | ₹94.1cr | 0.03 | C·X |
  | Hydraulic Line | 24.5% | 2,40,000 | ₹11.8cr | 0.12 | C·X |

  Landing Gear Actuator is the forecasting target because it's both highest-value AND low-volatility (not because it fails most often — Brake Assembly does that).

- **Key empirical finding:** landing severity (load, braking force at touchdown) drives actuator failure, NOT weather/runway condition. Runway condition barely moves failure rate (dry 59.6%, wet 60.9%, snowy 58.6%). Load quintiles show a 0%→100% failure-rate swing from lightest to heaviest landings. Robustness-checked by recomputing the load–failure correlation separately per runway condition: 0.814 dry / 0.823 wet / 0.827 snowy — stays constant, which rules out weather as a hidden confound. This contradicts the original abstract's assumption that weather was the dominant driver.

- **Correlation heatmap (all 4 parts):** values as shown in the report's Figure 3:
  | Factor | Brake Assembly | Landing Gear Actuator | Wheel Unit | Hydraulic Line |
  |---|---|---|---|---|
  | landing_cycles | 0.22 | 0.72 | 0.43 | 0.28 |
  | load_during_landing | 0.27 | **0.82** | 0.46 | 0.23 |
  | taxiing_duration | -0.01 | -0.00 | -0.02 | 0.01 |
  | speed_during_landing | 0.08 | 0.24 | 0.15 | 0.10 |
  | braking_force | 0.46 | 0.48 | **0.66** | 0.14 |
  | tire_pressure | -0.13 | -0.44 | -0.26 | -0.14 |
  | hydraulic_pressure | 0.01 | -0.00 | 0.01 | **-0.52** |

  Load/braking force are the strongest predictors for Landing Gear Actuator, Wheel Unit and Brake Assembly, but NOT for Hydraulic Line (its strongest is hydraulic_pressure, -0.52). Brake Assembly's correlations are all weak (max 0.46), probably because it fails 95% of the time, so there's little variation to explain. `taxiing_duration` predicts nothing (~0.00 everywhere). Note that for the Actuator, landing_cycles (0.72) is only a bit weaker than load (0.82), so avoid saying severity is "far better" than flight cycles. The report's Figure 3 caption ("strongest predictors for every tracked part") overstates this.

- **Apriori companion-parts rules** (min_support=0.15, min_lift=1.05):
  | Rule | Support | Confidence | Lift |
  |---|---|---|---|
  | Hydraulic Line → Landing Gear Actuator | 0.18 | 0.72 | 1.20 |
  | Landing Gear Actuator → Wheel Unit | 0.57 | 0.95 | 1.17 |
  | Hydraulic Line → Wheel Unit | 0.21 | 0.87 | 1.07 |

- **Business case (AOG cost vs holding cost), 18-hour assumed stockout duration:**
  | Scenario | AOG cost/hr | Cost per avoided event |
  |---|---|---|
  | Low (narrowbody, domestic) | ₹9,60,000 | ₹1.73cr |
  | Mid (narrowbody, typical) | ₹43,20,000 | ₹7.78cr |
  | High (widebody, peak) | ₹1,44,00,000 | ₹25.92cr |

  Holding cost for 4 spare actuators (25%/yr carrying cost) = ₹43.2 lakh/year. Even the low scenario costs ~4x the entire year's holding cost per event.

## File map

- `src/load_real_data.py` — loads the raw xlsx, maps flags→parts, writes `data/processed/landing_events.csv` and `data/processed/parts_master.csv`.
- `src/analysis_pipeline.py` — the main pipeline: EDA charts, baseline, ABC/XYZ classification, Apriori, business case. Writes to `reports/figures/` and `reports/docs/`. **Run `load_real_data.py` first.**
- `src/graph1_runway_condition.py`, `src/graph2_correlation_heatmap.py`, `src/graph4_baseline_benchmark.py` — standalone teaching copies of individual charts from the pipeline, each opens a live matplotlib window (`plt.show()`) so the user can run and tweak them directly.
- `src/architecture_diagram.py` — generates the system architecture diagram (linear mandatory path: Dataset → Preprocessing → Value/Volatility Classification → Demand Forecast Model (LightGBM) → Cost & Reorder Engine → Supplier Dashboard, with Companion-Parts Mining (Apriori) as a dashed OPTIONAL branch). Outputs `reports/figures/00_architecture.png` and `reports/Architecture_Diagram.png`. Diagram text deliberately avoids "ABC/XYZ" (says "Value/Volatility Classification" instead) and avoids ₹/INR — both per explicit user instruction, scoped only to this diagram.
- `src/generate_synthetic_data.py` — OLD placeholder script, no longer used downstream, kept for history only. (Useful reference: it shows **Brake Assembly** was the originally-assumed "most critical part". In that script every replacement event starts with Brake Assembly, and the Actuator was a rare 7% add-on. Once real data arrived, classification picked **Landing Gear Actuator** as the forecasting target instead. This matches the report and deck.)
- `reports/Midterm_Report_DemandForecasting_DimpalShetty.docx` — canonical generated report (15 sections, Abstract + ToC, built via a Node.js `docx`-package script).
- `reports/2024_MT_13052_Midterm_Dissertation.docx` — user's manually-edited renamed copy. **See "Open items" above — has unresolved content gaps, do not edit without asking.**
- `reports/Midterm_Viva_DimpalShetty.pptx` — 16-slide viva deck with speaker notes baked into each slide's Notes pane, built with python-pptx (matches the Claude Artifact deck's content/design). Ready to upload to Google Drive → "Open with Google Slides" for a native editable copy.
- `dashboard/` — Phase 7 supplier dashboard. `build_dashboard.py` reads the Phase 5/6 CSVs, re-checks yearly costs against Phase 6 (assert), and injects the data into `dashboard_template.html`, writing **`supplier_dashboard.html`**: a single offline file (no CDN, works in a viva without internet). **Layout (changed 2026-11-08 at user's request: suppliers shouldn't pick models):** Section 1 "Supplier view" always uses LightGBM, with no model dropdown. Controls: batch slider, AOG scenario, order cost. Tiles: forecast, stock to keep, safety buffer, EOQ order plan, actual outcome, "ship together" (Actuator→Wheel Unit 95%). It also has a stock-vs-demand line chart, the Apriori bundling panel, and a "What the words mean" glossary. Section 2 "For evaluation (viva/report only)" has a method comparison table (MAE 0.30 / 0.10 / fair baseline 6.18, buffer, shortages, yearly cost) and the yearly-cost bar chart. Then the assumptions list. Light/dark mode. Rebuild order: load_real_data → phase5 → phase6 → build_dashboard.
- `src/phase5_lightgbm.py`, `src/phase6_reorder_engine.py` — see Phase 5/6 sections above. Python env: `.venv` (Python 3.12 64-bit), `requirements.txt`.

## Literature referenced (all verified as real papers)

- **Bacchetti & Saccani (2012)** — documents the gap between academic spare-parts classification research and real MRO practice; motivates testing assumptions on real data.
- **Lagoda & Klumpp (2024)** — modified ABC-XYZ that integrates forecasting into classification rather than treating them as separate steps; precedent for this project's classify-then-forecast structure.
- **Olmo & Domingo** — ML (LightGBM) framework for aerospace rotable-parts demand forecasting using fleet-usage data; closest comparable paper to this project (see "gap" framing below). LightGBM was their best model in 94% of SKUs tested.
- **Stanton (2025)** — compares hand-picked ML models vs AutoML on real/synthetic Airbus landing-gear data; backs up the choice to reason through model selection (LightGBM) rather than running AutoML.
- **Agrawal & Srikant (1994)** — the original Apriori paper; directly implemented by the companion-parts mining module (same support/confidence/lift concepts).
- **Ke et al. (2017)** — the original LightGBM paper (GOSS + EFB techniques); justifies the speed/accuracy tradeoff behind the model choice.

**This project's gap vs. Olmo & Domingo specifically:** they forecast broadly across many rotable parts with general fleet-usage data; this project adds a prioritization step (classify first, forecast only the one part worth it), isolates one specific driver (landing severity vs weather) with a robustness check, adds a companion-parts bundling module, and extends all the way to a cost-based reorder decision — while using a smaller public dataset vs their presumably larger real fleet data (an honest limitation to acknowledge, not hide).

## Why LightGBM (already settled — don't re-litigate the choice, just recall the reasoning if asked)

No time sequence in the data (no dates/aircraft IDs) rules out ARIMA/Prophet/LSTM/Transformer. Small tabular dataset favors tree-based models over deep learning (Grinsztajn et al. 2022). Among tree models, gradient boosting (sequential error-correction) beats Random Forest (independent-tree averaging). Among gradient boosting libraries, LightGBM beats XGBoost on speed with equal accuracy (Ke et al. 2017's GOSS + EFB techniques). Independently validated in the closest comparable domain study (Olmo & Domingo).

**For Phase 5:** this will be a **regression** model (predicting a count — "how many units needed per batch" — not a classification model), to stay consistent with how the baseline and business case are framed.

## Git state

Remote `origin` = https://github.com/Shreyasc13/Dimpal-Dissertation-Final.git, branch `master`. Note: someone once committed the whole `.venv` folder by accident and then reverted it (commits d6cbc65/e173f7e), so keep `.venv` out of commits.
