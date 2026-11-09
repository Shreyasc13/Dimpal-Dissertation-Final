"""
Builds the FINAL viva deck: reports/Final_Viva_DimpalShetty.pptx

Same design as the midterm deck (reports/Midterm_Viva_DimpalShetty.pptx):
13.33 x 7.5 in, navy title slides, cream content slides, teal section label,
EB Garamond headings, IBM Plex Sans body text, white rounded cards, and
spoken speaker notes on every slide.

Every number here comes from reports/docs/*.csv (Phase 5/6 outputs) and was
checked against the final report. Re-run after changing any result.

Upload the .pptx to Google Drive -> "Open with Google Slides" for an
editable copy (Google Slides has both fonts built in).
"""
from pathlib import Path

from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

ROOT = Path(__file__).resolve().parent.parent
FIG = ROOT / "reports" / "figures"
OUT = ROOT / "reports" / "Final_Viva_DimpalShetty.pptx"

# ---- Design tokens (copied from the midterm deck) ----
NAVY = RGBColor(0x1F, 0x38, 0x64)
CREAM = RGBColor(0xFA, 0xF9, 0xF6)
TEAL = RGBColor(0x3F, 0x8C, 0x9E)
ORANGE = RGBColor(0xD9, 0x8C, 0x3A)
BODY = RGBColor(0x3A, 0x43, 0x50)
SUBHEAD = RGBColor(0x5A, 0x64, 0x72)
MUTED = RGBColor(0x8A, 0x94, 0xA3)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
CARD_LINE = RGBColor(0xE3, 0xE6, 0xE4)
ROW_ALT = RGBColor(0xEF, 0xEE, 0xEA)
ON_NAVY = RGBColor(0xC9, 0xD6, 0xE0)
ON_NAVY_MUTED = RGBColor(0x9F, 0xB4, 0xC6)
ON_NAVY_LABEL = RGBColor(0x7F, 0xA8, 0xBD)
GREEN = RGBColor(0x2E, 0x7D, 0x4F)
RED = RGBColor(0xC0, 0x39, 0x2B)
SERIF, SANS = "EB Garamond", "IBM Plex Sans"

prs = Presentation()
prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
BLANK = prs.slide_layouts[6]
page_no = 0


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def rect(slide, x, y, w, h, fill, line=None, rounded=False):
    shp = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE if rounded else MSO_SHAPE.RECTANGLE,
                                 Inches(x), Inches(y), Inches(w), Inches(h))
    if rounded:
        shp.adjustments[0] = 0.06
    shp.fill.solid()
    shp.fill.fore_color.rgb = fill
    if line is None:
        shp.line.fill.background()
    else:
        shp.line.color.rgb = line
        shp.line.width = Pt(1)
    shp.shadow.inherit = False
    return shp


def card(slide, x, y, w, h, fill=WHITE):
    return rect(slide, x, y, w, h, fill, CARD_LINE if fill == WHITE else fill, rounded=True)


def text(slide, x, y, w, h, paras, font=SANS, size=14, color=BODY, bold=False,
         align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, spacing=1.15, space_after=6):
    """paras: a string, or a list of strings / (text, {overrides}) / list-of-runs."""
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = Inches(0.05)
    tf.margin_top = tf.margin_bottom = Inches(0.03)
    if isinstance(paras, str):
        paras = [paras]
    for i, para in enumerate(paras):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.line_spacing = spacing
        p.space_after = Pt(space_after)
        runs = para if isinstance(para, list) else [para]
        for run in runs:
            t, o = (run, {}) if isinstance(run, str) else run
            r = p.add_run()
            r.text = t
            f = r.font
            f.name = o.get("font", font)
            f.size = Pt(o.get("size", size))
            f.bold = o.get("bold", bold)
            f.color.rgb = o.get("color", color)
    return tb


def bullets(slide, x, y, w, h, items, size=14, color=BODY):
    return text(slide, x, y, w, h, ["•  " + it for it in items], size=size, color=color,
                space_after=8)


def picture(slide, path, x, y, w, h):
    """Fit an image inside the box, keeping its shape, centred."""
    iw, ih = Image.open(path).size
    scale = min(w / iw, h / ih)
    pw, ph = iw * scale, ih * scale
    return slide.shapes.add_picture(str(path), Inches(x + (w - pw) / 2), Inches(y + (h - ph) / 2),
                                    Inches(pw), Inches(ph))


def table(slide, x, y, col_widths, rows, size=13, row_h=0.5, bold_rows=(), header_h=None):
    nrows, ncols = len(rows), len(rows[0])
    header_h = header_h or row_h
    shp = slide.shapes.add_table(nrows, ncols, Inches(x), Inches(y),
                                 Inches(sum(col_widths)), Inches(header_h + row_h * (nrows - 1)))
    tbl = shp.table
    tbl.first_row = True
    for j, cw in enumerate(col_widths):
        tbl.columns[j].width = Inches(cw)
    for i, row in enumerate(rows):
        tbl.rows[i].height = Inches(header_h if i == 0 else row_h)
        for j, val in enumerate(row):
            cell = tbl.cell(i, j)
            cell.fill.solid()
            cell.fill.fore_color.rgb = NAVY if i == 0 else (WHITE if i % 2 else ROW_ALT)
            cell.margin_left = cell.margin_right = Inches(0.1)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            tf = cell.text_frame
            tf.word_wrap = True
            p = tf.paragraphs[0]
            r = p.add_run()
            r.text = str(val)
            r.font.name = SANS
            r.font.size = Pt(size)
            r.font.bold = (i == 0) or (i in bold_rows)
            r.font.color.rgb = WHITE if i == 0 else BODY
    return tbl


def notes(slide, script):
    slide.notes_slide.notes_text_frame.text = script.strip()


def content_slide(label, title, title_size=30):
    global page_no
    page_no += 1
    s = prs.slides.add_slide(BLANK)
    rect(s, 0, 0, 13.333, 7.5, CREAM)
    text(s, 0.9, 0.55, 11.0, 0.5, label, size=15, color=TEAL, bold=True)
    text(s, 0.9, 1.05, 11.5, 1.0, title, font=SERIF, size=title_size, color=NAVY, bold=True)
    text(s, 0.9, 7.05, 1.0, 0.4, str(page_no), size=14, color=MUTED)
    return s


def navy_slide():
    s = prs.slides.add_slide(BLANK)
    rect(s, 0, 0, 13.333, 7.5, NAVY)
    return s


# ---------------------------------------------------------------------------
# Slides
# ---------------------------------------------------------------------------
# 0. Title
s = navy_slide()
text(s, 0.9, 1.3, 11.0, 0.5, "S1-26_SSZG628T · Dissertation Final Viva", size=15, color=ON_NAVY_LABEL, bold=True)
text(s, 0.9, 2.0, 11.3, 2.0, "Demand Forecasting In Inventory Management", font=SERIF, size=42, color=CREAM, bold=True)
text(s, 0.9, 3.9, 10.8, 1.0, "A spare-parts demand forecast for a landing-gear part, turned into a stock and order decision",
     size=18, color=ON_NAVY)
text(s, 0.9, 6.7, 6.5, 0.5, "Dimpal Shetty · 2024MT13052 · M.Tech Software Systems", size=13, color=ON_NAVY_MUTED)
text(s, 6.4, 6.7, 6.0, 0.5, "Airbus India Pvt Ltd, Bengaluru · Supervisor: Saurabh Mahajan", size=13,
     color=ON_NAVY_MUTED, align=PP_ALIGN.RIGHT)
notes(s, """
Good morning. Thank you for the time today. I'm presenting my final dissertation on demand forecasting for aircraft spare parts, carried out at Airbus India in Bengaluru under Saurabh Mahajan.
In one line: I built a pipeline that picks the spare part worth forecasting, forecasts how many will be needed, and turns that forecast into how many to keep on the shelf and how many to order.
""")

# 1. Contents
s = content_slide("OVERVIEW", "Contents", 38)
items = ["Introduction & Objectives", "Literature Review & Gap", "Data & Methodology",
         "Analysis & Prioritisation", "Model Training & Tuning", "Reorder Engine & Cost",
         "Supplier Dashboard", "Feedback, Limitations & Conclusions"]
for i, it in enumerate(items):
    col, row = i % 2, i // 2
    x, y = 0.9 + col * 5.9, 2.2 + row * 1.05
    text(s, x, y, 0.8, 0.6, f"{i + 1:02d}", font=SERIF, size=26, color=ORANGE, bold=True)
    text(s, x + 0.8, y + 0.05, 4.9, 0.6, it, size=18)
notes(s, """
I've split the talk into eight short parts. First the problem and objectives, then related work, the data and method, the analysis that chose the part to forecast, the model training and tuning, the reorder engine that turns the forecast into a stock decision, the supplier dashboard, and finally feedback, limitations and conclusions.
""")

# 2. Introduction
s = content_slide("1 · INTRODUCTION", "Static schedules can't see how an aircraft is actually operated", 27)
card(s, 0.9, 2.3, 5.4, 2.0)
text(s, 1.2, 2.5, 4.9, 0.5, "Under-stock", font=SERIF, size=22, color=RED, bold=True)
text(s, 1.2, 3.1, 4.9, 1.1, "Missing part → Aircraft On Ground (AOG) → costly, disruptive downtime", size=15)
card(s, 6.6, 2.3, 5.4, 2.0)
text(s, 6.9, 2.5, 4.9, 0.5, "Overstock", font=SERIF, size=22, color=TEAL, bold=True)
text(s, 6.9, 3.1, 4.9, 1.1, "Excess spares → money tied up in parts that may never be needed", size=15)
card(s, 0.9, 4.65, 11.1, 1.55, fill=NAVY)
text(s, 1.2, 4.85, 10.6, 1.2,
     [[("Problem: ", {"bold": True, "color": ORANGE}),
       ("how can landing-by-landing data be used to forecast demand for a high-value landing-gear part, "
        "and turn that forecast into a stock decision that balances the cost of running out against the cost of holding stock?",
        {"color": CREAM})]], size=15)
notes(s, """
Airlines face two opposite risks. If a part is missing, the aircraft is grounded, which is called AOG, and that costs lakhs to crores per event. If they keep too many spares, money is tied up on the shelf.
Today most parts are reordered on a fixed flight-hour or flight-cycle schedule, which treats every aircraft the same. My question was: can we use how each landing actually went to forecast demand, and then decide how much stock to keep?
""")

# 3. Objectives
s = content_slide("1 · INTRODUCTION", "Objectives", 34)
objs = ["Classify spare parts by value and demand predictability, to pick the part worth forecasting",
        "Build, tune and fairly test a demand model for that part, against a baseline and a second model",
        "Find which spare parts are usually flagged together, for supplier bundling",
        "Turn the forecast into a stock and order recommendation in rupees, weighing AOG cost against holding cost",
        "Show the result in a supplier dashboard"]
for i, o in enumerate(objs):
    y = 2.0 + i * 0.95
    card(s, 0.9, y, 11.5, 0.8)
    text(s, 1.1, y + 0.12, 0.6, 0.6, str(i + 1), font=SERIF, size=22, color=ORANGE, bold=True)
    text(s, 1.8, y + 0.18, 8.9, 0.6, o, size=14.5)
    text(s, 10.9, y + 0.18, 1.3, 0.5, "Done", size=14, color=GREEN, bold=True, align=PP_ALIGN.RIGHT)
notes(s, """
These are the five objectives, and all five are now complete. At the midterm, objectives one and three were done. Since then I've finished the model, the reorder engine and the dashboard.
""")

# 4. Literature review
s = content_slide("2 · LITERATURE REVIEW", "Prior work", 34)
table(s, 0.9, 2.0, [3.0, 4.4, 4.1], [
    ["Author (Year)", "Focus", "Relevance here"],
    ["Bacchetti & Saccani (2012)", "Gap between spare-parts research and practice", "Why methods must be tested on real records"],
    ["Lagoda & Klumpp (2024)", "ABC-XYZ linked to forecasting", "Same classify-then-forecast idea"],
    ["Olmo & Domingo (2026)", "Aerospace rotable parts forecasting with usage data", "Closest study; LightGBM was their best model"],
    ["Stanton et al. (2025)", "ML vs AutoML on landing-gear data", "Supports comparing more than one model"],
    ["Agrawal & Srikant (1994)", "Apriori algorithm", "Used for companion-part mining"],
    ["Ke et al. (2017)", "LightGBM gradient boosting", "Main forecasting model"],
], size=12.5, row_h=0.6)
notes(s, """
Six papers shaped the project. Bacchetti and Saccani showed that many spare-parts methods are never tested on real records. Lagoda and Klumpp link classification to forecasting, which is the structure I follow. Olmo and Domingo is the closest study: they forecast aerospace rotable parts using fleet-usage data, and LightGBM was their best model. Stanton compared several models on landing-gear data. Apriori and LightGBM are the two methods I use directly.
""")

# 5. Gap
s = content_slide("2 · LITERATURE REVIEW", "Current practice vs. what this project adds", 30)
card(s, 0.9, 2.2, 5.4, 4.0)
text(s, 1.2, 2.4, 4.9, 0.5, "Today", font=SERIF, size=20, color=SUBHEAD, bold=True)
bullets(s, 1.2, 3.0, 4.9, 3.0, ["Fixed flight-hour / cycle reorder schedule",
                                "Parts ranked only by cost, not predictability",
                                "Safety stock is a fixed buffer, rarely revisited",
                                "Companion parts bundled from experience, not data"], size=14)
card(s, 6.6, 2.2, 5.8, 4.0, fill=NAVY)
text(s, 6.9, 2.4, 5.3, 0.5, "What this project adds", font=SERIF, size=20, color=ORANGE, bold=True)
bullets(s, 6.9, 3.0, 5.3, 3.1, ["Classify first, forecast only the part worth it",
                                "Measures which landing condition drives failure, with a weather check",
                                "Companion-part rules for bundled orders",
                                "Goes all the way to a cost-based stock and order decision, plus a dashboard"],
        size=14, color=CREAM)
notes(s, """
On the left is how it's done today. On the right is what I add compared with Olmo and Domingo: a prioritisation step, a measured driver of failure with a check against weather, companion-part bundling, and a full chain to a stock decision.
The honest weakness compared with them is the data: they had real fleet data, and I used a small public dataset.
""")

# 6. Pipeline
s = content_slide("3 · DATA & METHODOLOGY", "Pipeline", 34)
card(s, 0.9, 2.0, 11.5, 4.6)
picture(s, FIG / "00_architecture.png", 1.1, 2.1, 11.1, 4.4)
notes(s, """
This is the full pipeline. The data is prepared, the value and volatility classification picks the part, the LightGBM model forecasts its demand, and the cost and reorder engine turns that into stock and order numbers shown on the supplier dashboard. Companion-part mining is an optional side branch that feeds bundling suggestions into the dashboard.
""")

# 7. Dataset and batches
s = content_slide("3 · DATA & METHODOLOGY", "Dataset and planning periods", 30)
card(s, 0.9, 2.2, 5.6, 4.0)
text(s, 1.2, 2.4, 5.1, 0.5, "The dataset", font=SERIF, size=20, color=SUBHEAD, bold=True)
text(s, 1.2, 2.95, 5.1, 1.0, "Public Kaggle dataset: 10,000 landings, 8 landing conditions and 4 yes/no failure flags.", size=14)
table(s, 1.2, 3.9, [2.7, 1.3], [["Part (flag)", "Flag rate"], ["Brake Assembly", "95.3%"],
                                ["Landing Gear Actuator", "59.7%"], ["Wheel Unit", "81.7%"],
                                ["Hydraulic Line", "24.5%"]], size=12, row_h=0.42)
card(s, 6.8, 2.2, 5.6, 4.0)
text(s, 7.1, 2.4, 5.1, 0.5, "No dates, so: batches", font=SERIF, size=20, color=SUBHEAD, bold=True)
bullets(s, 7.1, 3.0, 5.1, 3.1, ["No dates or aircraft IDs in the data",
                                "Every 200 landings = one planning period",
                                "50 batches, about 36 days each (at an assumed 2,000 landings a year)",
                                "Demand = number of actuator flags in a batch"], size=14)
notes(s, """
The data is a public Kaggle dataset of 10,000 landings. Each landing has eight conditions, like load, braking force and runway condition, and four yes/no failure flags, which I mapped to four parts.
There are no dates, so I can't plan by month. Instead, every 200 landings counts as one planning period. That gives 50 periods, each about 36 days if a fleet does 2,000 landings a year, which is an assumption.
""")

# 8. Data check
s = content_slide("3 · DATA & METHODOLOGY", "Data check: each failure flag follows a fixed rule", 30)
table(s, 0.9, 2.1, [2.8, 4.4], [["Part", "Flag = 1 when"],
                                ["Landing Gear Actuator", "load > 70 or cycles > 401"],
                                ["Wheel Unit", "braking force > 40 or cycles > 300"],
                                ["Brake Assembly", "braking force > 35 or cycles > 351.5"],
                                ["Hydraulic Line", "hydraulic pressure < 2800 or cycles > 450.5"]],
      size=13, row_h=0.6)
text(s, 0.9, 5.25, 7.2, 0.8, "Each rule matches all 10,000 rows. Found by fitting a two-split decision tree to each flag.",
     size=12.5, color=MUTED)
card(s, 8.5, 2.1, 3.9, 4.1, fill=NAVY)
text(s, 8.75, 2.3, 3.4, 0.5, "What it means", font=SERIF, size=20, color=ORANGE, bold=True)
bullets(s, 8.75, 2.9, 3.4, 3.2, ["The dataset is simulated",
                                 "Models can learn the rule exactly, so errors are near zero",
                                 "The contribution is the method; real airline data is needed to confirm the numbers"],
        size=13.5, color=CREAM)
notes(s, """
I want to raise this myself. When the models came out almost perfect, I checked why. Each failure flag follows a simple two-part rule, and the rule matches every single row. For the actuator, it's load above 70 or cycles above 401.
So the dataset is simulated. That's why the model errors are so small. My contribution is the method, the full pipeline from data to stock decision, and it can be re-run unchanged on real airline data, which is needed to confirm the size of the benefit.
""")

# 9. Drivers
s = content_slide("4 · ANALYSIS & PRIORITISATION", "What drives actuator failure in this data", 30)
card(s, 0.9, 2.2, 6.8, 4.0)
picture(s, FIG / "01_env_brake_temp.png", 1.0, 2.3, 6.6, 3.8)
card(s, 8.0, 2.2, 4.4, 4.0, fill=NAVY)
text(s, 8.25, 2.4, 3.9, 1.0, "Runway condition barely moves it: dry 59.6%, wet 60.9%, snowy 58.6%.", size=13.5, color=CREAM)
text(s, 8.25, 3.35, 3.9, 1.0, "Landing load moves it from near 0% to near 100%.", size=14, color=ORANGE, bold=True)
text(s, 8.25, 4.2, 3.9, 1.9, "Weather check: the load-failure link is the same on every runway (0.814 dry, 0.823 wet, 0.827 snowy).",
     size=13, color=ON_NAVY)
notes(s, """
At the midterm, the feedback was to prove whether weather plays a role. On the left, failure rate by runway condition is almost flat. By landing load, it goes from near zero to near one hundred percent.
To check that load isn't just standing in for weather, I measured the load-failure link separately for dry, wet and snowy runways: 0.814, 0.823 and 0.827, almost identical. So in this data, weather is not the driver. Given the data check, this reflects how the simulator was built, so it should be confirmed on real data.
""")

# 10. Classification
s = content_slide("4 · ANALYSIS & PRIORITISATION", "Value / Volatility classification", 30)
card(s, 0.9, 2.2, 6.4, 4.0)
picture(s, FIG / "04_abc_xyz_matrix.png", 1.0, 2.3, 6.2, 3.8)
rows = [("Landing Gear Actuator", "Class A·X · ₹516.0 cr · 59.7% flag rate", True),
        ("Brake Assembly", "Class B·X · ₹329.3 cr · 95.3% flag rate", False),
        ("Wheel Unit", "Class C·X · ₹94.1 cr · 81.7% flag rate", False),
        ("Hydraulic Line", "Class C·X · ₹11.8 cr · 24.5% flag rate", False)]
for i, (name, desc, hi) in enumerate(rows):
    y = 2.2 + i * 1.03
    card(s, 7.6, y, 4.8, 0.88, fill=NAVY if hi else WHITE)
    text(s, 7.85, y + 0.08, 4.4, 0.4, name, size=14, bold=True, color=ORANGE if hi else NAVY)
    text(s, 7.85, y + 0.45, 4.4, 0.4, desc, size=12.5, color=CREAM if hi else BODY)
notes(s, """
The value and volatility classification ranks parts by yearly value and by how steady their demand is. The Landing Gear Actuator is the only Class A·X part: the highest value with steady demand. So it's the part worth forecasting.
It wasn't picked because it fails most; the brake assembly fails more often. Before the data, I'd assumed the brake assembly would be the main part, and the classification changed that. The rupee values use assumed unit costs and 2,000 landings a year.
""")

# 11. Companion parts
s = content_slide("4 · ANALYSIS & PRIORITISATION", "Companion parts (Apriori)", 30)
table(s, 0.9, 2.1, [5.6, 1.9, 2.1, 1.9], [["Rule", "Support", "Confidence", "Lift"],
                                          ["Hydraulic Line → Landing Gear Actuator", "0.18", "0.72", "1.20"],
                                          ["Landing Gear Actuator → Wheel Unit", "0.57", "0.95", "1.17"],
                                          ["Hydraulic Line → Wheel Unit", "0.21", "0.87", "1.07"]],
      size=14, row_h=0.6, bold_rows=(2,))
card(s, 0.9, 4.8, 11.5, 1.4, fill=NAVY)
text(s, 1.2, 5.0, 11.0, 1.1,
     [[("Most useful for a supplier: ", {"bold": True, "color": ORANGE}),
       ("when the actuator is flagged, the wheel unit is flagged 95% of the time, so the two can be shipped together.",
        {"color": CREAM})]], size=15)
notes(s, """
Apriori finds parts that are flagged on the same landing. Support is how often the pair appears, confidence is how often the second part comes with the first, and lift above one means the link is stronger than chance.
The most useful rule is actuator to wheel unit: 95% of the time they go together. The dashboard turns this into a ship-together suggestion.
""")

# 12. Model setup
s = content_slide("5 · MODEL TRAINING & TUNING", "How the model was built and tested", 30)
cols = [("Why LightGBM", ["No dates, so time-series models (ARIMA, Prophet, LSTM) don't fit",
                          "Tree models beat deep learning on small tabular data",
                          "Best model in the closest study",
                          "Random Forest trained the same way, for comparison"]),
        ("What it predicts", ["Chance of actuator failure for each landing, from its 8 conditions",
                              "Other failure flags are not used as inputs",
                              "Chances added up per batch = actuators needed"]),
        ("Fair testing and tuning", ["5 folds of 10 batches: train on 40, test on 10 never seen",
                                     "Settings tuned only inside the training batches",
                                     "LightGBM: 12 setting combinations tried; Random Forest: 6"])]
for i, (head, its) in enumerate(cols):
    x = 0.9 + i * 3.9
    card(s, x, 2.2, 3.7, 4.2)
    text(s, x + 0.25, 2.4, 3.2, 0.5, head, font=SERIF, size=19, color=ORANGE, bold=True)
    bullets(s, x + 0.25, 3.0, 3.25, 3.3, its, size=13)
notes(s, """
Three points on the model. Why LightGBM: there are no dates, so time-series models like ARIMA, Prophet or LSTM don't fit. Tree models usually beat deep learning on small tables, and LightGBM was the best model in the closest study. I trained Random Forest the same way to check that choice.
What it predicts: for every landing, the chance the actuator fails, using only the eight conditions. Adding up the chances in a batch gives the number of actuators needed.
Testing: the batches are split into five groups. Each time, the model learns from 40 batches and is tested on 10 it has never seen. Tuning, meaning choosing the settings, is done only on the training batches, so the test stays fair.
""")

# 13. Results
s = content_slide("5 · MODEL TRAINING & TUNING", "Results: forecast error per batch", 30)
card(s, 0.9, 2.2, 6.4, 4.0)
picture(s, FIG / "08_phase5_mae_comparison.png", 1.0, 2.3, 6.2, 3.8)
tiles = [("6.18", "Baseline (training-batch average)", WHITE, NAVY),
         ("0.30", "LightGBM, tuned", NAVY, ORANGE),
         ("0.10", "Random Forest, tuned", WHITE, NAVY)]
for i, (num, lab, fill, numc) in enumerate(tiles):
    y = 2.2 + i * 1.37
    card(s, 7.6, y, 4.8, 1.2, fill=fill)
    text(s, 7.85, y + 0.12, 1.6, 0.9, num, font=SERIF, size=34, color=numc, bold=True, anchor=MSO_ANCHOR.MIDDLE)
    text(s, 9.45, y + 0.15, 2.8, 0.9, lab, size=14, color=CREAM if fill == NAVY else BODY, anchor=MSO_ANCHOR.MIDDLE)
text(s, 0.9, 6.35, 11.5, 0.6, "Average miss in actuators per batch of 200 landings (MAE). The midterm's 5.52 averaged all 50 batches, including the one being predicted.",
     size=12, color=MUTED)
notes(s, """
This is the main result. The error is the average miss per batch of 200 landings. The fair baseline, which just predicts the average, misses by about 6 actuators. LightGBM misses by 0.3 and Random Forest by 0.1.
At the midterm I showed 5.52 for the baseline. That number averaged all batches including the one being predicted, so it was slightly flattering. 6.18 is the fair version.
Random Forest was slightly better here. The simulated rule has a sharp cut-off, and fully grown trees match sharp cut-offs exactly. The gap is less than one unit per 200 landings, so it makes no practical difference.
""")

# 14. What the model learned
s = content_slide("5 · MODEL TRAINING & TUNING", "What the model relies on", 30)
card(s, 0.9, 2.2, 6.4, 4.0)
picture(s, FIG / "09_phase5_feature_importance.png", 1.0, 2.3, 6.2, 3.8)
card(s, 7.6, 2.2, 4.8, 4.0, fill=NAVY)
text(s, 7.85, 2.4, 4.3, 0.5, "Feature importance", font=SERIF, size=20, color=ORANGE, bold=True)
bullets(s, 7.85, 3.0, 4.3, 3.1, ["Landing load: 99.1%", "Landing cycles: 0.7%",
                                 "Runway condition: 0.0%",
                                 "Matches the rule found in the data check: the model learned the right inputs"],
        size=14, color=CREAM)
notes(s, """
Feature importance shows which inputs the model used. Load is 99.1%, landing cycles 0.7%, and runway condition zero. That matches the rule from the data check, so the model picked up the right inputs and ignored the rest. It's also a second confirmation that weather plays no role in this data.
""")

# 15. Reorder rule
s = content_slide("6 · REORDER ENGINE & COST", "Turning the forecast into a stock level", 30)
card(s, 0.9, 2.2, 6.2, 4.0)
text(s, 1.2, 2.4, 5.7, 0.5, "The stock rule", font=SERIF, size=20, color=SUBHEAD, bold=True)
text(s, 1.2, 3.0, 5.7, 0.6, "Stock to keep = forecast + z × typical error", size=16, color=NAVY, bold=True)
bullets(s, 1.2, 3.75, 5.7, 2.4, ["z compares two costs (newsvendor rule):",
                                 "Being 1 unit short = one AOG event, ₹1.73 cr to ₹25.92 cr",
                                 "1 extra unit on the shelf for one batch = ₹1.08 lakh",
                                 "AOG costs far more, so the rule aims to almost never run out"], size=13.5)
table(s, 7.4, 2.2, [1.6, 2.1, 1.3], [["Scenario", "Target in stock", "z"],
                                     ["Low", "99.38%", "2.50"], ["Mid", "99.86%", "2.99"],
                                     ["High", "99.96%", "3.34"]], size=14, row_h=0.62)
text(s, 7.4, 4.9, 5.0, 1.2, "“Typical error” is measured only on other folds, never on the batch being planned.",
     size=12.5, color=MUTED)
notes(s, """
A forecast alone isn't a decision. Before each batch, the shelf is filled up to the forecast plus a safety buffer. The buffer is z times the model's typical error.
z comes from comparing two costs. Running one unit short means one AOG event, which costs between 1.7 and 26 crore depending on the scenario. Keeping one extra actuator for one batch costs about 1.08 lakh. Because running short is so much more expensive, the rule aims to have stock 99.4 to 99.96 percent of the time.
""")

# 16. Cost results
s = content_slide("6 · REORDER ENGINE & COST", "Same protection, far less stock", 30)
card(s, 0.9, 2.2, 6.4, 4.0)
picture(s, FIG / "10_phase6_total_cost.png", 1.0, 2.3, 6.2, 3.8)
facts = [("Safety buffer (Mid)", "22.8 → 2.0 units"), ("Batches short", "0 of 50, every method"),
         ("Yearly cost (Mid)", "₹2.46 cr → ₹0.21 cr")]
for i, (k, v) in enumerate(facts):
    y = 2.2 + i * 0.9
    card(s, 7.6, y, 4.8, 0.78)
    text(s, 7.85, y + 0.17, 2.2, 0.5, k, size=13, color=SUBHEAD)
    text(s, 9.9, y + 0.15, 2.4, 0.5, v, size=14, bold=True, color=NAVY, align=PP_ALIGN.RIGHT)
card(s, 7.6, 4.95, 4.8, 1.25, fill=NAVY)
text(s, 7.85, 5.05, 4.3, 1.1, [[("Saving with LightGBM: ", {"bold": True, "color": ORANGE}),
                                ("about ₹1.84 to 2.52 crore a year, depending on the AOG scenario", {"color": CREAM})]],
     size=14)
text(s, 0.9, 6.35, 11.5, 0.6, "50 batches is too few to test rare stockouts fully. Costs use assumed unit cost, holding rate and 2,000 landings a year.",
     size=12, color=MUTED)
notes(s, """
I replayed all 50 batches for each method. No method ran short in any batch. So the whole saving comes from keeping fewer spare units for the same protection: with LightGBM, the buffer drops from about 23 units to 2.
In the mid scenario, yearly cost falls from 2.46 crore to 0.21 crore. Across scenarios, the saving is about 1.8 to 2.5 crore a year.
Two honest caveats: 50 batches is too few to test rare stockouts properly, and the costs rest on assumed unit costs and fleet usage.
""")

# 17. EOQ
s = content_slide("6 · REORDER ENGINE & COST", "How much to order at a time (EOQ)", 30)
table(s, 0.9, 2.2, [2.6, 1.8, 2.0, 2.2], [["Cost per order", "Units per order", "Orders per year", "Orders per batch"],
                                          ["₹25,000", "7", "171", "17"],
                                          ["₹50,000 (main)", "11", "109", "11"],
                                          ["₹1,00,000", "15", "80", "8"],
                                          ["₹2,00,000", "21", "57", "6"]], size=14, row_h=0.6, bold_rows=(2,))
card(s, 9.9, 2.2, 2.5, 3.0, fill=NAVY)
text(s, 10.1, 2.4, 2.1, 2.7, ["Balances ordering cost against holding cost.",
                              "Same for every method: the forecast's value is in the safety buffer."],
     size=13, color=CREAM, space_after=10)
text(s, 0.9, 5.45, 11.5, 0.8, "Yearly demand about 1,194 actuators; holding cost ₹10.8 lakh per unit per year. Cost per order is not known, so a range is shown.",
     size=12.5, color=MUTED)
notes(s, """
The midterm promised an order-size formula too. EOQ, the economic order quantity, balances the cost of placing an order against the cost of holding stock. At an assumed 50,000 rupees per order, the best order is 11 units, about 11 orders per batch. I don't know the real order cost, so the table shows a range.
EOQ is the same whichever forecast is used, because they all predict the same yearly total. The forecast earns its value in the safety buffer, not the order size.
""")

# 18. Dashboard
s = content_slide("7 · SUPPLIER DASHBOARD", "Supplier dashboard", 34)
card(s, 0.9, 2.0, 5.2, 4.75)
picture(s, ROOT / "reports" / "final_report" / "figures" / "12_dashboard_supplier_view.png", 1.0, 2.1, 5.0, 4.55)
card(s, 6.4, 2.0, 6.0, 3.0)
text(s, 6.7, 2.15, 5.5, 0.5, "Supplier view (LightGBM only)", font=SERIF, size=19, color=SUBHEAD, bold=True)
bullets(s, 6.7, 2.7, 5.5, 2.3, ["Forecast, stock to keep, safety buffer",
                                "Order plan (EOQ) and what actually happened",
                                "Ship together: Wheel Unit (95%)",
                                "Pick batch, AOG scenario, order cost"], size=13.5)
card(s, 6.4, 5.2, 6.0, 1.55, fill=NAVY)
text(s, 6.7, 5.3, 5.5, 1.4, [[("Evaluation section: ", {"bold": True, "color": ORANGE}),
                              ("model comparison kept separate, for the viva only. A single offline HTML file: no internet needed.",
                               {"color": CREAM})]], size=13.5)
notes(s, """
This is the supplier dashboard. The supplier only sees what they need: the forecast, how much stock to keep, the safety buffer, the order plan, and which part to ship together. They don't choose a model; it always uses LightGBM.
The model comparison sits in a separate section marked for evaluation. It's one HTML file that works offline, so I can show it live now if you'd like.
""")

# 19. Feedback
s = content_slide("8 · FEEDBACK, LIMITATIONS & CONCLUSIONS", "Midterm feedback: how it was addressed", 30)
table(s, 0.9, 2.1, [4.0, 7.5], [["Feedback", "What was done"],
                                ["Prove whether weather plays a role", "Same load-failure link on every runway (0.814 / 0.823 / 0.827); runway importance 0.0% in the model"],
                                ["Business case analysis", "Reorder engine weighing AOG cost against holding cost; yearly cost per scenario in rupees"],
                                ["Current-solution & gap analysis", "Current practice compared with the closest study (Olmo & Domingo); four added steps"]],
      size=13, row_h=0.95, header_h=0.55)
notes(s, """
At the midterm I received three points of feedback. On weather: I showed the load-failure link is the same on every runway, and the model gives runway condition zero importance. On the business case: it's now a full reorder engine with yearly costs in rupees. On the gap analysis: I compared current practice and the closest study, and listed the four things this project adds.
""")

# 20. Limitations
s = content_slide("8 · FEEDBACK, LIMITATIONS & CONCLUSIONS", "Limitations", 32)
lims = ["No dates: batches of 200 landings stand in for planning periods",
        "A flag means a problem was detected, not that the part was replaced",
        "Simulated demand level (about 119 actuators per 200 landings) is far above real aircraft",
        "Costs and 2,000 landings a year are assumptions, not Airbus figures",
        "50 batches are too few to test rare stockouts",
        "Orders assumed to arrive before each batch; real lead times are longer"]
for i, l in enumerate(lims):
    col, row = i % 2, i // 2
    x, y = 0.9 + col * 5.85, 2.1 + row * 1.4
    card(s, x, y, 5.65, 1.2)
    text(s, x + 0.25, y + 0.15, 5.2, 0.95, l, size=14, anchor=MSO_ANCHOR.MIDDLE)
notes(s, """
These are the main limitations. There are no dates, so batches stand in for time. A flag probably means a problem was detected, not that the part was replaced. The demand level is far higher than real aircraft. All costs and the fleet usage are assumptions. Fifty batches can't fully test rare stockouts. And I assumed orders arrive before each batch, while real lead times can be long.
""")

# 21. Conclusions
s = content_slide("8 · FEEDBACK, LIMITATIONS & CONCLUSIONS", "Conclusions and next steps", 30)
card(s, 0.9, 2.1, 6.0, 4.3)
text(s, 1.2, 2.3, 5.5, 0.5, "Conclusions", font=SERIF, size=20, color=SUBHEAD, bold=True)
bullets(s, 1.2, 2.9, 5.5, 3.5, ["Full pipeline built: data → classification → forecast → stock and order decision → dashboard",
                                "Actuator picked as the only Class A·X part",
                                "Error cut from 6.18 to 0.30 (LightGBM) and 0.10 (Random Forest)",
                                "Buffer cut from about 23 to 2 units, no stockouts, ₹1.8 to 2.5 cr a year saved"],
        size=13.5)
card(s, 7.2, 2.1, 5.2, 4.3, fill=NAVY)
text(s, 7.45, 2.3, 4.7, 0.5, "Next steps", font=SERIF, size=20, color=ORANGE, bold=True)
bullets(s, 7.45, 2.9, 4.7, 3.5, ["Re-run on real airline records with dates and confirmed replacements",
                                 "Use real costs, fleet usage and supplier lead times",
                                 "Re-check LightGBM vs Random Forest on real data",
                                 "Extend to more parts"], size=13.5, color=CREAM)
notes(s, """
To conclude: I built the full pipeline from raw data to a stock and order decision, shown in a dashboard. The classification picked the actuator. The models cut the forecast error from about 6 units to under one. And the reorder engine turned that into a much smaller safety buffer, saving an estimated 1.8 to 2.5 crore a year with no stockouts in the test.
The most important next step is to run the same pipeline on real airline records, with real costs and lead times. Thank you, I'm happy to take questions.
""")

# 22. Thank you
s = navy_slide()
text(s, 0.9, 3.0, 11.0, 1.2, "Thank you", font=SERIF, size=48, color=CREAM, bold=True)
text(s, 0.9, 4.2, 11.0, 0.6, "Questions welcome", size=18, color=ON_NAVY)
text(s, 0.9, 6.7, 6.5, 0.5, "Airbus India Pvt Ltd, Bengaluru", size=13, color=ON_NAVY_MUTED)
text(s, 6.4, 6.7, 6.0, 0.5, "Supervisor: Saurabh Mahajan", size=13, color=ON_NAVY_MUTED, align=PP_ALIGN.RIGHT)
notes(s, "Thank you. I'm happy to take questions, and I can show the dashboard live if that helps.")

prs.save(OUT)
print(f"Wrote {OUT} with {len(prs.slides)} slides")
