import pandas as pd

from make_model import normalizer as N

GRID = pd.read_csv('data/model_grid.csv')


def run(s):
    out = N.sanitize(pd.DataFrame({'vehicle_number': ['X'], 'make/model': [s]}), GRID)
    return None if out.empty else out.iloc[0]


def test_basic_cleanup():
    r = run('TATA MOTORS LTD/LPT 25.18 TC BSIV')
    assert r.sanitized_make == 'TATA' and r.final_model == '2518'


def test_upto_rows_dropped():
    assert run('TATA MOTORS LTD/GVW upto 16200') is None


def test_first_match_trap_and_best_match_fix():
    raw = 'DAIMLER INDIA COMMERCIAL VEHICLES PVT. LTD'
    assert N.OEM_categorisation(raw) == 'VE COMMERCIAL'   # the original rule gets this wrong
    assert N.OEM_best_match(raw) == 'DAIMLER'
