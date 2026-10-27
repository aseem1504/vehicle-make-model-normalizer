"""Synthetic VAHAN-style maker/model strings with a known right answer.

The messiness copies what the original notebooks had to deal with: legal-entity suffixes,
typos in the maker name, dots and dashes inside model codes, body-type noise, BS emission
tags, rows with 'upto' ranges, Excel dates in the text column and blanks. Registration
numbers are fake (state code + random digits).
"""
import random

import pandas as pd

MAKERS = {
    'TATA': ['TATA MOTORS LTD', 'TATA MOTORS LIMITED', 'TATA MOTOR LTD', 'M/S TATA MOTORS', 'TATA MOTORS LTD.'],
    'ASHOK LEYLAND': ['ASHOK LEYLAND LTD', 'ASHOK LEYLAND LIMITED', 'ASHOK LEYLEND LTD', 'ASHOKLEYLAND LTD'],
    'MAHINDRA': ['MAHINDRA & MAHINDRA LIMITED', 'MAHINDRA AND MAHINDRA LTD', 'MAHINDRA NAVISTAR AUTOMOTIVES LTD'],
    'VE COMMERCIAL': ['VE COMMERCIAL VEHICLES LTD', 'V E COMMERCIAL VEHICLES LIMITED', 'VECV LTD'],
    'DAIMLER': ['DAIMLER INDIA COMMERCIAL VEHICLES PVT. LTD', 'DAIMLER INDIA COMM VEHICLES PVT LTD'],
    'EICHER': ['EICHER MOTORS LTD', 'EICHER MOTORS LIMITED'],
    'SML ISUZU': ['SML ISUZU LIMITED', 'SML ISUZU LTD'],
    'FORCE': ['FORCE MOTORS LIMITED'],
}
MODELS = {
    'TATA': [('LPT 2518', '2518'), ('LPT 3118', '3118'), ('LPK 2518 TIPPER', '2518'), ('LPT 1613', '1613'),
             ('SIGNA 4825.TK', 'SIGNA 4825'), ('SIGNA 4923.S', 'SIGNA 4923'), ('LPT 4018 CAB', '4018'),
             ('ACE HT', 'ACE'), ('407 PICKUP', 'PICKUP 407'), ('LPT 709 EX', '709'), ('ULTRA 1918.T', 'ULTRA 1918'),
             # newer models that are NOT in data/model_grid.csv yet
             ('LPT 1916', '1916'), ('SIGNA 5530.S', 'SIGNA 5530')],
    'ASHOK LEYLAND': [('2518 IL', '2518'), ('U 3118 IL', '3118'), ('4019 IL TRACTOR', '4019'), ('DOST PLUS', 'DOST'),
                      ('ECOMET 1615 HE', 'ECOMET 1615'), ('16.16 IL', '1616'), ('BOSS 1616 LE', 'BOSS 1616'),
                      ('2214-IL', '2214'), ('AVTR 4220', 'AVTR 4220')],
    'MAHINDRA': [('BLAZO 40 TRACTOR', 'BLAZO40'), ('BLAZO 25 HAULAGE', 'BLAZO25'), ('BOLERO PICK UP', 'BOLERO PICKUP'),
                 ('FURIO 14', 'FURIO'), ('BLAZO.49', 'BLAZO49'), ('TORRO 25', 'TORRO25')],
    'VE COMMERCIAL': [('EICHER PRO 3015', 'PRO 3015'), ('PRO 3015 XP', 'PRO 3015'), ('EICHER 1109 HD', '1109')],
    'DAIMLER': [('BHARATBENZ 3123R', '3123'), ('BHARATBENZ 2523C', '2523'), ('BHARATBENZ 1617R', '1617'),
                ('BB 4028T', '4028'), ('BHARATBENZ 2823C', '2823'), ('BHARATBENZ 5528TT', '5528')],
    'EICHER': [('PRO 1110', 'PRO'), ('11.10', None)],
    'SML ISUZU': [('SAMRAT GS', None), ('SARTAJ', None)],
    'FORCE': [('TRAVELLER 26', None)],
}
NOISE = ['', ' BSIV', ' BS-VI', ' BS III', ' CBC', ' HSD', ' (TRUCK)', ' GOODS CARRIER']
STATES = ['MH', 'GJ', 'RJ', 'HR', 'UP', 'MP', 'KA', 'TN', 'DL', 'PB']


def make_rows(n=4000, seed=5):
    random.seed(seed)
    rows = []
    for k in range(n):
        vrn = f"{random.choice(STATES)}{random.randint(1, 50):02d}XX{random.randint(0, 9999):04d}"
        roll = random.random()
        if roll < 0.03:
            rows.append((vrn, None, None, None))
            continue
        if roll < 0.05:
            rows.append((vrn, pd.Timestamp('2019-04-01'), None, None))
            continue
        make = random.choice(list(MAKERS))
        raw_make = random.choice(MAKERS[make])
        raw_model, true_model = random.choice(MODELS[make])
        if roll < 0.07:
            raw_model = 'GVW upto 16200 KG'
            true_model = None
        if random.random() < 0.15:
            raw_model = raw_model.replace(' ', '.', 1)
        s = f"{raw_make}/{raw_model}{random.choice(NOISE)}"
        if random.random() < 0.25:
            s = s.replace('/', ' / ')
        rows.append((vrn, s, make, true_model))
    return pd.DataFrame(rows, columns=['vehicle_number', 'make/model', 'true_make', 'true_model'])
