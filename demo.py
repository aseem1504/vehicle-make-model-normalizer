"""Score the original make/model pipeline on synthetic VAHAN strings.

    python demo.py
"""
import os

import pandas as pd

from make_model import normalizer as N
from make_model.simulate import make_rows

pd.set_option('display.width', 200)
os.makedirs('outputs', exist_ok=True)

grid = pd.read_csv('data/model_grid.csv')
raw = make_rows()
raw.to_csv('outputs/vahan_strings_synthetic.csv', index=False)
print(f"{len(raw)} raw strings, e.g.:")
for s in raw['make/model'].dropna().astype(str).sample(6, random_state=1):
    print("   ", s)


def tokens(x):
    return set(str(x).split()) if isinstance(x, str) and x.strip() else set()


def score(out):
    j = raw.merge(out[['vehicle_number', 'sanitized_make', 'final_model']], on='vehicle_number', how='left')
    usable = j['true_make'].notna()
    make_ok = (j.loc[usable, 'sanitized_make'] == j.loc[usable, 'true_make']).mean()
    has_model = j['true_model'].notna()
    model_ok = j[has_model].apply(lambda r: tokens(r['final_model']) == tokens(r['true_model']), axis=1).mean()
    junk = ~usable | j['true_model'].isna()
    junk_dropped = j.loc[junk, 'final_model'].isna().mean()
    return make_ok, model_ok, junk_dropped, j


print("\n=== Original pipeline (fuzzy OEM threshold 70, first match wins) ===")
out = N.sanitize(raw[['vehicle_number', 'make/model']], grid)
make_ok, model_ok, junk, j = score(out)
print(f"make correct: {make_ok:.1%} | model correct: {model_ok:.1%} | junk rows left without a model: {junk:.1%}")
wrong = j[j.true_make.notna() & (j.sanitized_make != j.true_make)]
print("\nMost common make mistakes:")
print(wrong.assign(raw_make=wrong['make/model'].str.split('/').str[0].str.strip())
      .groupby(['raw_make', 'sanitized_make']).size().sort_values(ascending=False).head(8).to_string())

print("\n=== Threshold sweep: first-match (original) vs best-match ===")
rows = []
for t in [50, 60, 70, 80, 90]:
    first = N.sanitize(raw[['vehicle_number', 'make/model']], grid, oem_threshold=t)
    best = first.copy()
    best['sanitized_make'] = best['make'].apply(lambda x: N.OEM_best_match(x, t))
    rows.append({'threshold': t, 'first_match_make_acc': round(score(first)[0], 3),
                 'best_match_make_acc': round(score(best)[0], 3)})
print(pd.DataFrame(rows).to_string(index=False))

out.to_csv('outputs/make_model_clean.csv', index=False)
print("\nClean output written to outputs/make_model_clean.csv")
