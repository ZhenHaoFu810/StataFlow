"""M01-LIN-002: Minimal reproduction — near-collinear regressors.

Stata 17 detects near-collinearity and omits x1. Python stataflow retains
both x1 and x2, producing a different model and unstable coefficients.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from stataflow import OLS


def main():
    rng = np.random.default_rng(20260613)
    n = 50
    x1 = rng.normal(size=n)
    # x2 is x1 plus tiny noise, then scaled by 1e6
    x2 = (x1 + rng.normal(scale=1e-7, size=n)) * 1e6
    y = 1.0 + 2.0 * x1 + 3.0 * x2 + rng.normal(scale=0.5, size=n)
    df = pd.DataFrame({"y": y, "x1": x1, "x2": x2})

    print("Correlation(x1, x2):", np.corrcoef(x1, x2)[0, 1])
    print()

    res = OLS(df, y="y", x=["x1", "x2"], add_constant=True).fit(vce="ols")
    print("Python stataflow coefficients:")
    for c in res.coefficients:
        print(f"  {c.name}: beta={c.beta:.6g}, se={c.std_err:.6g}")
    print()
    print("Python dropped vars:", getattr(res._model, "_collinear_dropped", []))
    print()
    print("Stata 17 output (expected):")
    print("  note: x1 omitted because of collinearity.")
    print("  x2: beta ~= 3e-6, se ~= small")
    print("  _cons: beta ~= 1")


if __name__ == "__main__":
    main()
