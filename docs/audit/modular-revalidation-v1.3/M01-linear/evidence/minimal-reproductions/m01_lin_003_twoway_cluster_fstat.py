"""M01-LIN-003: Minimal reproduction — two-way cluster F-statistic.

Stata 17 reports e(F) equal to the OLS F-statistic (using residual df)
when vce(cluster) has two dimensions. Python stataflow reports the
cluster-robust Wald F (using the cluster VCE and min-cluster df).
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from stataflow.compat.stata import regress


def main():
    rng = np.random.default_rng(20260613)
    n_firms = 30
    n_years = 20
    n = n_firms * n_years
    firm = np.repeat(np.arange(n_firms), n_years)
    year = np.tile(np.arange(n_years), n_firms)
    x = rng.normal(size=n)
    y = 1.0 + 2.0 * x + rng.normal(scale=0.5, size=n)
    df = pd.DataFrame({"y": y, "x": x, "firm": firm, "year": year})

    res = regress(df, y="y", x=["x"], vce="cluster", cluster=["firm", "year"])
    print("Python stataflow two-way cluster result:")
    print(f"  nobs={res.sample.nobs}")
    print(f"  df_resid={res.fit.df_resid}")
    print(f"  f_stat={res.fit.f_stat:.4f}")
    print(f"  f_pvalue={res.fit.f_pvalue:.6g}")
    for c in res.coefficients:
        print(f"  {c.name}: beta={c.beta:.6g}, se={c.std_err:.6g}")
    print()
    print("Stata 17 equivalent:")
    print("  regress y x, vce(cluster firm year)")
    print("  Expected e(F) ~= OLS F(1, n-2), not Wald F = t^2")


if __name__ == "__main__":
    main()
