"""M01-LIN-001: Minimal reproduction — aweight=0 handling.

Stata 17 drops observations with aweight=0 and completes the regression.
Python stataflow raises ValueError before fitting.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from pathlib import Path
import sys

# Add project root so we can import stataflow
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from stataflow.compat.stata import regress
from stataflow import OLS


def main():
    df = pd.DataFrame({
        "y": [1.0, 2.0, 3.0, 4.0, 5.0],
        "x": [1.0, 2.0, 3.0, 4.0, 5.0],
        "w": [1.0, 1.0, 0.0, 1.0, 1.0],  # third observation has zero weight
    })

    print("Data:")
    print(df)
    print()

    # Stata 17 command: regress y x [aweight=w]
    # Expected: nobs=4, zero-weight observation dropped.

    print("Python OLS with aweight=0:")
    try:
        res = OLS(df, y="y", x=["x"], weights=df["w"].values, weight_type="aweight").fit()
        print(f"  nobs={res.sample.nobs}")
        print(f"  beta_x={res.coefficients[0].beta}")
    except Exception as e:
        print(f"  ERROR: {type(e).__name__}: {e}")

    print()
    print("Python regress() wrapper with aweight=0:")
    try:
        res = regress(df, y="y", x=["x"], aweight="w")
        print(f"  nobs={res.sample.nobs}")
        print(f"  beta_x={res.coefficients[0].beta}")
    except Exception as e:
        print(f"  ERROR: {type(e).__name__}: {e}")


if __name__ == "__main__":
    main()
