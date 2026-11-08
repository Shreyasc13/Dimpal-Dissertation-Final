# Final report (LaTeX)

`main.tex` is the full final dissertation report. It follows the BITS WILP
"Guidelines for preparation of WILP Project Report (06.04.2022)":
9" x 11" page, 1" margins, double spacing, Roman page numbers before the
Introduction and Arabic after, decimal numbering, abstract under 200 words,
references numbered in citation order, and a glossary with page numbers.

## How to make the PDF (Overleaf, free)

1. Go to overleaf.com and log in.
2. **New Project → Upload Project** and choose `final_report_overleaf.zip`.
3. Click **Recompile**. It uses pdfLaTeX, which is the default, so nothing needs changing.
   The table of contents and glossary page numbers fill in automatically.
4. Download the PDF. It must be **10 MB or less** (it should be about 2 MB).

## Things you must fill in

Everything you still need to fill in shows in the PDF as **red text on yellow**.
In `main.tex`, search for `\fillin`. There are 13:

| Where | What to fill in |
|---|---|
| Top of file (`\SubmitMonth`) | Month and year of submission. This appears on the cover and title page. |
| Cover | Station name and centre |
| Acknowledgements | Head of the organisation (name and designation) |
| Acknowledgements | Professional expert / in-charge of the project (or delete the line) |
| Acknowledgements and abstract sheet | Faculty mentor's name (2 places) |
| Abstract sheet | Duration, date of start, date of submission |
| Abstract sheet | Designations of Saurabh Mahajan and Karthik Mahadevan |
| References [12] | Kaggle dataset author, exact title, and the date you downloaded it |

## Before you submit

- Ask your supervisor to read the draft. The guidelines require this.
- Sign the abstract sheet. Only the signature page should be a scanned image; everything else must stay as text.
- Copy all the text from the PDF into Notepad. If it pastes as readable text, the report passes the "text format" check.
- To show the rupee symbol instead of "Rs.", follow the comment near `\INR` at the top of `main.tex`.

## Rebuilding the batch table

Appendix C (forecasts for every batch) was generated from
`reports/docs/phase5_batch_predictions.csv` and `phase6_batch_decisions_mid.csv`.
If you re-run Phase 5/6, that table and the numbers in the text must be updated.
