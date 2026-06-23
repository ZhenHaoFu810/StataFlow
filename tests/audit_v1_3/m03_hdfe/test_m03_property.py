"""M03 HDFE: metamorphic / property tests."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from audit_utils import save_evidence

from stataflow import AbsorbingOLS


def _make_balanced_2fe(seed: int = 42, n_firm: int = 30, n_time: int = 5) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    firm = np.repeat(np.arange(1, n_firm + 1), n_time)
    year = np.tile(np.arange(1, n_time + 1), n_firm)
    alpha = rng.normal(0, 1, n_firm)[firm - 1]
    gamma = rng.normal(0, 0.5, n_time)[year - 1]
    x = rng.normal(0, 1, n_firm * n_time)
    y = 1.0 + 1.5 * x + alpha + gamma + rng.normal(0, 0.5, n_firm * n_time)
    return pd.DataFrame({"firm": firm, "year": year, "y": y, "x": x})


def property_p1_absorb_label_invariance():
    """Absorb variable labels renamed one-to-one should not change estimates."""
    test_id = "P1_absorb_label_invariance"
    df = _make_balanced_2fe(seed=1)
    base = AbsorbingOLS(df, y="y", x=["x"], absorb=["firm", "year"], add_constant=True, drop_singletons=True).fit(vce="ols")
    base_coef = {c.name: c.beta for c in base.coefficients}

    df2 = df.copy()
    df2["firm"] = df2["firm"].map(lambda f: f"F{f:03d}")
    df2["year"] = df2["year"].map(lambda t: f"Y{t:03d}")
    renamed = AbsorbingOLS(df2, y="y", x=["x"], absorb=["firm", "year"], add_constant=True, drop_singletons=True).fit(vce="ols")
    renamed_coef = {c.name: c.beta for c in renamed.coefficients}

    ok = all(np.isclose(base_coef[n], renamed_coef[n], rtol=1e-10) for n in base_coef)
    msg = "absorb labels invariant" if ok else f"coefs changed: {base_coef} vs {renamed_coef}"
    save_evidence(test_id, {"base": base_coef, "renamed": renamed_coef}, None, [(ok, msg)])
    return ok, msg


def property_p2_redundant_absorb_fe():
    """Adding a perfectly redundant copy of an absorb variable should leave slope unchanged."""
    test_id = "P2_redundant_absorb_fe"
    df = _make_balanced_2fe(seed=2)
    base = AbsorbingOLS(df, y="y", x=["x"], absorb=["firm", "year"], add_constant=True, drop_singletons=True).fit(vce="ols")
    base_slope = next(c.beta for c in base.coefficients if c.name == "x")

    df2 = df.copy()
    df2["firm_copy"] = df2["firm"]
    redundant = AbsorbingOLS(df2, y="y", x=["x"], absorb=["firm", "firm_copy", "year"], add_constant=True, drop_singletons=True).fit(vce="ols")
    redundant_slope = next(c.beta for c in redundant.coefficients if c.name == "x")

    ok = np.isclose(base_slope, redundant_slope, rtol=1e-6)
    msg = f"redundant FE slope unchanged: base={base_slope} redundant={redundant_slope}"
    save_evidence(test_id, {"base_slope": base_slope, "redundant_slope": redundant_slope}, None, [(ok, msg)])
    return ok, msg


def property_p3_scale_invariance():
    """Scaling y and x by a constant leaves slope unchanged."""
    test_id = "P3_scale_invariance"
    df = _make_balanced_2fe(seed=3)
    base = AbsorbingOLS(df, y="y", x=["x"], absorb=["firm", "year"], add_constant=True, drop_singletons=True).fit(vce="ols")
    base_slope = next(c.beta for c in base.coefficients if c.name == "x")

    scale = 7.0
    df2 = df.copy()
    df2["y"] *= scale
    df2["x"] *= scale
    scaled = AbsorbingOLS(df2, y="y", x=["x"], absorb=["firm", "year"], add_constant=True, drop_singletons=True).fit(vce="ols")
    scaled_slope = next(c.beta for c in scaled.coefficients if c.name == "x")

    ok = np.isclose(base_slope, scaled_slope, rtol=1e-10)
    msg = f"slope invariant to scale: base={base_slope} scaled={scaled_slope}"
    save_evidence(test_id, {"base_slope": base_slope, "scaled_slope": scaled_slope}, None, [(ok, msg)])
    return ok, msg


def property_p4_row_order_invariance():
    """Shuffling rows should not change estimates."""
    test_id = "P4_row_order_invariance"
    df = _make_balanced_2fe(seed=4)
    base = AbsorbingOLS(df, y="y", x=["x"], absorb=["firm", "year"], add_constant=True, drop_singletons=True).fit(vce="ols")
    base_coef = {c.name: c.beta for c in base.coefficients}

    rng = np.random.default_rng(5)
    df2 = df.iloc[rng.permutation(len(df))].reset_index(drop=True)
    shuffled = AbsorbingOLS(df2, y="y", x=["x"], absorb=["firm", "year"], add_constant=True, drop_singletons=True).fit(vce="ols")
    shuffled_coef = {c.name: c.beta for c in shuffled.coefficients}

    ok = all(np.isclose(base_coef[n], shuffled_coef[n], rtol=1e-10) for n in base_coef)
    msg = "row order invariant" if ok else f"coefs changed: {base_coef} vs {shuffled_coef}"
    save_evidence(test_id, {"base": base_coef, "shuffled": shuffled_coef}, None, [(ok, msg)])
    return ok, msg


def main():
    tests = [
        property_p1_absorb_label_invariance,
        property_p2_redundant_absorb_fe,
        property_p3_scale_invariance,
        property_p4_row_order_invariance,
    ]
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
