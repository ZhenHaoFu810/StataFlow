import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
import pandas as pd
from stataflow.estimators.absorbing_ols import AbsorbingOLS

df = pd.read_csv("D:/OneDrive - SAIF/PhD3/StataFlow/research/data/public/panel/grunfeld.csv")
for col in ['firm', 'year', 'inv', 'value', 'capital']:
    df[col] = pd.to_numeric(df[col], errors='coerce')

print("Testing MAP path forced (PANEL-01)...")
try:
    model = AbsorbingOLS(data=df, y='inv', x=['value', 'capital'], absorb='firm', technique='map')
    result = model.fit(vce='ols')
    print("STATUS: SUCCESS (unexpected - MAP path should have crashed before fix)")
    print(f"N={result.sample.nobs}  df_m={result.fit.df_model}  df_r={result.fit.df_resid}")
    for c in result.coefficients:
        print(f"  {c.name:15s}  beta={c.beta:12.6f}  se={c.std_err:12.6f}")
except Exception as e:
    print(f"STATUS: ERROR ({type(e).__name__})")
    import traceback
    traceback.print_exc()
