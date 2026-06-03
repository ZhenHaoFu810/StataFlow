import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
import pandas as pd
from stataflow.compat.stata.hdfe import reghdfe

df = pd.read_csv("D:/OneDrive - SAIF/PhD3/StataFlow/research/data/public/panel/grunfeld.csv")
for col in ['firm', 'year', 'inv', 'value', 'capital']:
    df[col] = pd.to_numeric(df[col], errors='coerce')

result = reghdfe(df, y='inv', x=['value', 'capital'], absorb='firm', savefe=True)
print("Fixed effects from Python savefe:")
for var, series in result.fixed_effects.items():
    print(f"\n{var}:")
    for level, val in series.items():
        print(f"  firm_{int(level)}={val:.6f}")
