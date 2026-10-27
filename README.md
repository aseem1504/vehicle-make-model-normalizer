# Vehicle Make and Model Normalizer

Turn messy RTO registration strings like `TATA MOTORS LIMITED/LPT.2518 TC BSIV` into a clean `TATA 2518`.

Built in 2020 for a truck GPS fleet. All strings in this repo are synthetic.

## The problem

Every truck in India has a "maker / model" entry in the government vehicle registry (VAHAN). It is free text, typed at hundreds of RTOs over decades. The same truck model shows up dozens of ways:

```
TATA MOTORS LTD/LPT 2518 TC
TATA MOTOR LTD/LPT.2518 BSIV
M/S TATA MOTORS/LPK 2518 TIPPER
TATA MOTORS LIMITED / LPT 25.18
```

That breaks anything that groups by model. The business needed clean make and model to compare how different trucks are used, to build utilisation reports for lenders, and to match trucks to the right GPS installation and FASTag class.

## How it works

1. Drop junk rows: blanks, Excel dates sitting in the text column, and "GVW upto ..." range entries.
2. Split on `/` into maker and model.
3. Snap the maker to a known OEM list with fuzzy matching (`partial_ratio > 70`, first match wins).
4. Pull model codes out with one big regex built from a "grid" of known models (`data/model_grid.csv`). Four-digit codes also match with any separator, so `25.18`, `25-18` and `25 18` all become `2518`.
5. Clean each match (strip dots, dashes and spaces, uppercase, remove repeats), then join.

The grid is a living list. In the original, unmatched strings were pushed to a Google Sheet. A person added the right answer, and the next run picked it up.

## Results on synthetic data

`python demo.py` scores the pipeline on 4,000 synthetic VAHAN strings with known answers. Some newer models are left out of the grid on purpose.

- Make correct: **85%**
- Model correct: **93%** (the misses are the models not yet in the grid)
- Junk rows correctly left without a model: **100%**

The make errors are more interesting than the score:

| Raw maker | Became | Why |
|---|---|---|
| `DAIMLER INDIA COMMERCIAL VEHICLES PVT. LTD` | `VE COMMERCIAL` | "VE COMMERCIAL" sits earlier in the OEM list and scores over 70 on "...E COMMERCIAL..." |
| `M/S TATA MOTORS` | `M`, or worse, `VE COMMERCIAL` | the `/` inside "M/S" is read as the maker/model split, and a lone "M" fuzzy-matches anything with an M in it |
| `VECV LTD` | `VECV LTD` | an abbreviation that no fuzzy score will catch |

The first one is a rule-order bug. The rule takes the first OEM that clears the bar, not the best one. Switching to the best score, with nothing else changed, lifts make accuracy from 85% to 91%:

| Threshold | First match (original) | Best match |
|---|---|---|
| 50 | 82% | 91% |
| 70 | 85% | 91% |
| 90 | 91% | 91% |

## What the numbers say

Raising the threshold to 90 looks like a fix, but it only hides the ordering bug by refusing more matches. Best match gets the same score at any threshold, which means the result no longer depends on a number someone picked by hand.

The remaining 9% is a list problem, not a scoring one: aliases like VECV, and "M/S" prefixes. A short alias table beats any threshold tuning. The same goes for models. Recall is capped by how fresh the grid is, so the review loop that feeds it matters more than the regex.

This is also a good test bed for an LLM. Now that there is a labelled set and a baseline, any LLM-based normalizer can be scored against the same 4,000 strings, on accuracy and on cost per string.

## Run it

```bash
pip install -r requirements.txt
python demo.py
pytest
```

## Repo layout

```
make_model/
  normalizer.py   the pipeline, ported from the original, plus OEM_best_match (added)
  simulate.py     synthetic VAHAN strings with known answers
data/
  model_grid.csv  known model codes (the "grid")
notebooks/original/  the real notebooks, cleaned (see the README inside)
```

## What changed from the original code

- `(?i)` flags in the middle of a regex are an error since Python 3.11. Each text token is now wrapped as `(?i:TOKEN)`, which means the same thing.
- The original passed `'r' + pattern` to `findall`. That glued a literal "r" onto the first grid entry, so it could never match. Removed.
- `model_create` left a trailing space on every result. Stripped.
- `fuzzywuzzy` was swapped for `rapidfuzz`, which gives the same scores and installs cleanly.
- Google Sheets reads and writes were replaced with local CSVs.

## Data and privacy

All strings and registration numbers are synthetic. The fake registration numbers use an `XX` series. The original notebooks had their outputs, credentials, sheet links and hosts removed before upload.
