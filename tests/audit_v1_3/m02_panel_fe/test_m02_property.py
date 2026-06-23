"""M02 Panel/FE: metamorphic / property tests."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from audit_utils import save_evidence

from stataflow import FixedEffectsOLS


def _make_balanced_panel(seed: int = 42, n_entity: int = 50, n_time: int = 5) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    entities = np.repeat(np.arange(1, n_entity + 1), n_time)
    times = np.tile(np.arange(1, n_time + 1), n_entity)
    fe = rng.normal(0, 1, n_entity)[entities - 1]
    x = rng.normal(0, 1, n_entity * n_time) + 0.3 * fe
    y = 1.0 + 2.0 * x + fe + rng.normal(0, 0.5, n_entity * n_time)
    return pd.DataFrame({"entity": entities, "time": times, "y": y, "x": x})


def property_p1_entity_label_invariance():
    """Renaming entity labels must leave FE coefficient estimates unchanged."""
    test_id = "P1_entity_label_invariance"
    df = _make_balanced_panel(seed=1)
    base = FixedEffectsOLS(df, y="y", x=["x"], fe="entity", add_constant=True).fit(vce="ols")
    base_coef = {c.name: c.beta for c in base.coefficients}

    df2 = df.copy()
    df2["entity"] = df2["entity"].map(lambda e: f"E{e:03d}")
    renamed = FixedEffectsOLS(df2, y="y", x=["x"], fe="entity", add_constant=True).fit(vce="ols")
    renamed_coef = {c.name: c.beta for c in renamed.coefficients}

    ok = all(np.isclose(base_coef[n], renamed_coef[n], rtol=1e-10, atol=1e-10) for n in base_coef)
    msg = f"coefficients invariant under entity relabeling" if ok else f"coefficients changed: {base_coef} vs {renamed_coef}"
    save_evidence(test_id, {"base": base_coef, "renamed": renamed_coef}, None, [(ok, msg)])
    return ok, msg


def property_p2_time_reorder_invariance():
    """Shuffling time periods within each entity must leave slope estimates unchanged."""
    test_id = "P2_time_reorder_invariance"
    df = _make_balanced_panel(seed=2)
    base = FixedEffectsOLS(df, y="y", x=["x"], fe="entity", add_constant=True).fit(vce="ols")
    base_coef = {c.name: c.beta for c in base.coefficients}

    # Shuffle rows within each entity while preserving the entity column
    df2 = df.copy().reset_index(drop=True)
    rng = np.random.default_rng(3)
    idx = np.concatenate([rng.permutation(g.index.values) for _, g in df2.groupby("entity")])
    df2 = df2.iloc[idx].reset_index(drop=True)
    reordered = FixedEffectsOLS(df2, y="y", x=["x"], fe="entity", add_constant=True).fit(vce="ols")
    reordered_coef = {c.name: c.beta for c in reordered.coefficients}

    ok = all(np.isclose(base_coef[n], reordered_coef[n], rtol=1e-10, atol=1e-10) for n in base_coef)
    msg = f"coefficients invariant under time reorder" if ok else f"coefficients changed: {base_coef} vs {reordered_coef}"
    save_evidence(test_id, {"base": base_coef, "reordered": reordered_coef}, None, [(ok, msg)])
    return ok, msg


def property_p3_entity_invariant_dropped():
    """A regressor that is constant within entities should be dropped or have zero coefficient."""
    test_id = "P3_entity_invariant_dropped"
    df = _make_balanced_panel(seed=4)
    df["z"] = df.groupby("entity")["x"].transform("mean")  # entity-invariant
    df["z"] = df["z"] + 1e-12 * np.random.default_rng(5).normal(size=len(df))  # tiny jitter

    try:
        result = FixedEffectsOLS(df, y="y", x=["x", "z"], fe="entity", add_constant=True).fit(vce="ols")
        coefs = {c.name: c.beta for c in result.coefficients}
        se = {c.name: c.std_err for c in result.coefficients}
        ok = np.isclose(coefs.get("z", 0.0), 0.0, atol=1e-8) or np.isclose(se.get("z", 1.0), 0.0, atol=1e-12)
        msg = f"entity-invariant z handled: coef={coefs.get('z')} se={se.get('z')}"
        save_evidence(test_id, {"coefs": coefs, "se": se}, None, [(ok, msg)])
        return ok, msg
    except Exception as e:
        msg = f"entity-invariant regressor caused exception: {type(e).__name__}: {e}"
        save_evidence(test_id, {"error": str(e)}, None, [(False, msg)])
        return False, msg


def property_p4_scale_invariance():
    """Scaling y and all x by a constant must scale coefficients accordingly."""
    test_id = "P4_scale_invariance"
    df = _make_balanced_panel(seed=6)
    base = FixedEffectsOLS(df, y="y", x=["x"], fe="entity", add_constant=True).fit(vce="ols")
    base_coef = {c.name: c.beta for c in base.coefficients}

    scale = 7.0
    df2 = df.copy()
    df2["y"] *= scale
    df2["x"] *= scale
    scaled = FixedEffectsOLS(df2, y="y", x=["x"], fe="entity", add_constant=True).fit(vce="ols")
    scaled_coef = {c.name: c.beta for c in scaled.coefficients}

    # x slope should be unchanged; _cons unchanged (if it exists); SE scales by scale
    ok = np.isclose(base_coef["x"], scaled_coef["x"], rtol=1e-10)
    msg = f"slope invariant to scale: base={base_coef['x']} scaled={scaled_coef['x']}"
    save_evidence(test_id, {"base": base_coef, "scaled": scaled_coef}, None, [(ok, msg)])
    return ok, msg


def main():
    tests = [
        property_p1_entity_label_invariance,
        property_p2_time_reorder_invariance,
        property_p3_entity_invariant_dropped,
        property_p4_scale_invariance,
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
