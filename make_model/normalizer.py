"""Turn messy RTO / VAHAN "MAKER / MODEL" strings into a clean make + model.

Ported from notebooks/original/03_make_model_grid_regex.ipynb (grid version) and
01_make_model_vahan_fuzzy.ipynb (fuzzy correction step). Same steps, same thresholds.

Fixes needed to run on current Python / pandas, all small:
  * `(?i)` inline flags in the middle of a pattern are an error since Python 3.11, so each
    text token is wrapped as `(?i:TOKEN)` instead (same meaning)
  * the original passed `'r' + pattern` to findall, which glued a literal "r" onto the first
    alternative so the first grid entry could never match; removed
  * model_create left a trailing space on every output; stripped
  * fuzzywuzzy replaced by rapidfuzz (same partial_ratio scores, no C build issues)
"""
import re

import pandas as pd
from rapidfuzz import fuzz

OEM_LIST = ['ASHOK LEYLAND', 'TATA', 'VE COMMERCIAL', 'MAHINDRA', 'EICHER', 'DAIMLER', 'SML ISUZU',
            'VECTRA', 'Baldev', 'FORCE', 'PIAGGIO', 'MAN TRUCKS', 'AMW', 'GENERAL']

EXCLUSIVE_MODELS = ['torro25', 'traco35', 'truxo25', 'truxo31', 'torro.25', 'traco.35', 'truxo.25', 'truxo.31',
                    'Blazo37', 'Blazo25', 'Blazo40', 'Blazo49', 'Blazo.37', 'Blazo.25', 'Blazo.40', 'Blazo.49',
                    'load.king', 'loadking', 'pickup', 'pick.up']


def build_model_regex(grid):
    grid = grid[~grid['correction'].isin(['LPK', 'LPT'])]  # series prefixes, not models
    total = ''
    for i in grid[grid['type'].isin(['4 digs'])]['correction'].astype(str).unique():
        total += "|" + i[0:2] + r'\D' + i[2:4]   # 25.18 / 25-18 / 25 18
        total += "|" + i
    for i in grid[grid['type'].isin(['3 digs', '3 dig', '5 dig'])]['correction'].astype(str).unique():
        total += "|" + i
    for i in grid[grid['type'].isin(['text'])]['correction'].unique():
        total += "|" + "(?i:" + i + ")"
    for i in EXCLUSIVE_MODELS:
        total += "|" + "(?i:" + i + ")"
    return re.compile(total[1:])


def OEM_categorisation(x, threshold=70):
    """First OEM whose partial fuzzy score beats the threshold wins (order matters)."""
    for i in OEM_LIST:
        if fuzz.partial_ratio(x, i) > threshold:
            return i
    return x


def split_data(x):
    try:
        return ''.join(x.split('/')[1:])
    except Exception:
        return None


def model_create(model):
    if model is None:
        return None
    final = ''
    for i in model:
        i = re.sub(r'\.', '', i)
        i = re.sub('-', '', i)
        i = re.sub(' ', '', i)
        i = re.sub(':', '', i)
        i = re.sub(r"\*", '', i)
        i = i.upper()
        if i not in final.split(' '):
            final = final + " " + i
    alphabatecally = ''
    for i in reversed(sorted(final.split(' '))):
        alphabatecally = alphabatecally + " " + i
    return alphabatecally[1:].strip()


def fuzzy_comparision(model_string, final_models, threshold=95):
    """Snap a model to a known-good list (the 'final models' sheet in the original)."""
    for i in final_models:
        if fuzz.partial_ratio(model_string, i) > threshold:
            return i
    return model_string


def sanitize(make_model, grid, oem_threshold=70):
    """make_model: DataFrame with vehicle_number and 'make/model'."""
    mm = make_model.copy()
    mm = mm[mm['make/model'].notnull()]
    mm = mm[~mm['make/model'].isin([' ', ''])]
    mm.drop_duplicates('vehicle_number', inplace=True)
    # VAHAN exports sometimes carry an Excel date instead of text
    mm = mm[mm['make/model'].apply(lambda x: isinstance(x, str))]
    mm = mm[mm['make/model'].str.findall('upto').apply(len) == 0]

    mm['make'] = mm['make/model'].apply(lambda x: x.split('/')[0])
    mm = mm[mm['make'].str.findall(r'\d\d').apply(len) == 0]
    mm['model'] = mm['make/model'].apply(split_data)
    mm = mm[mm['model'].notnull()]

    rx = build_model_regex(grid)
    mm['model_regex'] = mm['model'].apply(lambda s: rx.findall(s) or None)
    mm['final_model'] = mm['model_regex'].apply(model_create)

    mm = mm[mm['make'].str.strip() != '']
    mm['sanitized_make'] = mm['make'].apply(lambda x: OEM_categorisation(x, oem_threshold))
    mm['final_make_model'] = mm['sanitized_make'] + ' ' + mm['final_model'].fillna('')
    return mm


def OEM_best_match(x, threshold=70):
    """Variant added for comparison: take the OEM with the highest score, not the first
    one over the line. Fixes cases where a short name like 'TATA' grabs a long string first."""
    scores = [(fuzz.partial_ratio(x, i), i) for i in OEM_LIST]
    best = max(scores)
    return best[1] if best[0] > threshold else x
