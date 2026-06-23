"""M04 IV/GMM: metamorphic / property tests."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from audit_utils import save_evidence

from stataflow import IV2SLS


def _make_iv_data(seed: int = 42, n: int = 100) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    z = rng.normal(0, 1, n)
    w = rng.normal(0, 1, n)
    u = rng.normal(0, 0.5, n)
    x = 0.5 * z + 0.2 * w + u + rng.normal(0, 0.3, n)
    y = 1.0 + 0.7 * w + 1.5 * x + u + rng.normal(0, 0.3, n)
    return pd.DataFrame({"y": y, "x": x, "w": w, "z": z})


def property_p1_instrument_label_invariance():
    """Renaming instrument labels one-to-one should not change estimates."""
    test_id = "P1_instrument_label_invariance"
    df = _make_iv_data(seed=1)
    base = IV2SLS(df, y="y", x_exog=["w"], x_endog=["x"], instruments=["z"], add_constant=True).fit(vce="robust")
    base_slope = next(c.beta for c in base.coefficients if c.name == "x")

    df2 = df.copy()
    df2 = df2.rename(columns={"z": "instrument_z"})
    renamed = IV2SLS(df2, y="y", x_exog=["w"], x_endog=["x"], instruments=["instrument_z"], add_constant=True).fit(vce="robust")
    renamed_slope = next(c.beta for c in renamed.coefficients if c.name == "x")

    ok = np.isclose(base_slope, renamed_slope, rtol=1e-10)
    msg = f"instrument label invariant: base={base_slope} renamed={renamed_slope}"
    save_evidence(test_id, {"base_slope": base_slope, "renamed_slope": renamed_slope}, None, [(ok, msg)])
    return ok, msg


def property_p2_scale_invariance():
    """Scaling y and all x by a constant leaves IV slope unchanged."""
    test_id = "P2_scale_invariance"
    df = _make_iv_data(seed=2)
    base = IV2SLS(df, y="y", x_exog=["w"], x_endog=["x"], instruments=["z"], add_constant=True).fit(vce="robust")
    base_slope = next(c.beta for c in base.coefficients if c.name == "x")

    scale = 4.0
    df2 = df.copy()
    df2["y"] *= scale
    df2["x"] *= scale
    df2["w"] *= scale
    scaled = IV2SLS(df2, y="y", x_exog=["w"], x_endog=["x"], instruments=["z"], add_constant=True).fit(vce="robust")
    scaled_slope = next(c.beta for c in scaled.coefficients if c.name == "x")

    ok = np.isclose(base_slope, scaled_slope, rtol=1e-10)
    msg = f"IV slope invariant to scale: base={base_slope} scaled={scaled_slope}"
    save_evidence(test_id, {"base_slope": base_slope, "scaled_slope": scaled_slope}, None, [(ok, msg)])
    return ok, msg


def property_p3_row_order_invariance():
    """Shuffling rows should not change IV estimates."""
    test_id = "P3_row_order_invariance"
    df = _make_iv_data(seed=3)
    base = IV2SLS(df, y="y", x_exog=["w"], x_endog=["x"], instruments=["z"], add_constant=True).fit(vce="robust")
    base_coef = {c.name: c.beta for c in base.coefficients}

    rng = np.random.default_rng(4)
    df2 = df.iloc[rng.permutation(len(df))].reset_index(drop=True)
    shuffled = IV2SLS(df2, y="y", x_exog=["w"], x_endog=["x"], instruments=["z"], add_constant=True).fit(vce="robust")
    shuffled_coef = {c.name: c.beta for c in shuffled.coefficients}

    ok = all(np.isclose(base_coef[n], shuffled_coef[n], rtol=1e-10) for n in base_coef)
    msg = "row order invariant" if ok else f"coefs changed: {base_coef} vs {shuffled_coef}"
    save_evidence(test_id, {"base": base_coef, "shuffled": shuffled_coef}, None, [(ok, msg)])
    return ok, msg


def main():
    tests = [property_p1_instrument_label_invariance, property_p2_scale_invariance, property_p3_row_order_invariance]
    summary = []
    for test in tests:
        print(f"\n=== Running {test.__name__} ===")
        try:
            passed, msg = test()
            print(f"{'PASS' if passed else 'FAIL'}: {msg}")
            summary.append((test.__name__, passed))
        except Exception as e:
            print(f"ERROR: {e}")
            import traceback
            traceback.print_exc()
            summary.append((test.__name__, False))
    print("\n=== Summary ===")
    for name, passed in summary:
        print(f"{name}: {'PASS' if passed else 'FAIL'}")


if __name__ == "__main__":
    main()
