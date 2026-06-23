import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import numpy as np
import pandas as pd
from tests.audit_v1_3.m06_ppmlhdfe.m06_audit_utils import run_stata_ppmlhdfe
from stataflow.estimators import PPMLHDFE

rng = np.random.default_rng(20260612)
n = 60
entity = np.repeat(np.arange(12), 5)
time = np.tile(np.arange(5), 12)
x1 = rng.normal(0, 1, n)
x2 = rng.normal(0, 1, n)
alpha = rng.normal(0, 0.5, 12)[entity]
eta = alpha + 0.8 * x1 - 0.5 * x2
y = rng.poisson(np.exp(eta))
df = pd.DataFrame({"y": y, "x1": x1, "x2": x2, "entity_id": entity, "time_id": time})

st = run_stata_ppmlhdfe(
    df,
    command="ppmlhdfe y x1 x2, absorb(entity_id) vce(robust)",
    y_var="y",
    prefix="probe_S1",
    coef_names=["x1", "x2", "_cons"],
    predict_types=["xb", "mu", "residuals"],
)
print("Stata parsed:", st)

py = PPMLHDFE(df, y="y", x=["x1","x2"], absorb=["entity_id"]).fit(vce="robust")
print("Python:", {c.name: (c.beta, c.std_err) for c in py.coefficients})
print("py nobs", py.sample.nobs, "df_a", py.fit.df_a, "ll", py.fit.ll, "deviance", py.fit.deviance, "pseudo_r2", py.fit.pseudo_r2)
