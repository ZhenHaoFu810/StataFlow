"""Tests for ResultSchema serialization and deserialization."""

import io
import json
from contextlib import redirect_stdout

import numpy as np
import pandas as pd
import pytest

from stataflow.results.result import (
    ResultSchema,
    ModelInfo,
    SampleInfo,
    FitInfo,
    CoefficientRow,
    VarianceInfo,
    DiagnosticsInfo,
    ProvenanceInfo,
)


def test_result_schema_defaults():
    """Test that ResultSchema can be created with defaults."""
    result = ResultSchema()
    assert result.model is not None
    assert result.sample is not None
    assert result.fit is not None
    assert result.coefficients == []
    assert result.variance is not None
    assert result.diagnostics is not None
    assert result.provenance is not None


def test_result_schema_to_dict():
    """Test serialization to dictionary."""
    result = ResultSchema()
    result.model = ModelInfo(command="regress", estimator_family="ols")
    result.sample = SampleInfo(nobs=100, n_input_rows=100)
    result.fit = FitInfo(df_model=2.0, df_resid=97.0, r2=0.5)
    result.coefficients = [
        CoefficientRow(name="x1", beta=1.5, std_err=0.2, t_stat=7.5, p_value=0.0),
    ]
    result.variance = VarianceInfo(
        row_names=["x1", "_cons"],
        values=[[0.04, 0.0], [0.0, 0.01]],
    )
    result.provenance = ProvenanceInfo(source="python", stata_version_target="17")

    d = result.to_dict()
    
    assert d["model"]["command"] == "regress"
    assert d["sample"]["nobs"] == 100
    assert d["fit"]["r2"] == 0.5
    assert len(d["coefficients"]) == 1
    assert d["coefficients"][0]["name"] == "x1"
    assert d["coefficients"][0]["beta"] == 1.5
    assert len(d["variance"]["row_names"]) == 2
    assert d["provenance"]["source"] == "python"


def test_result_schema_round_trip():
    """Test round-trip serialization: ResultSchema -> dict -> ResultSchema."""
    original = ResultSchema()
    original.model = ModelInfo(
        command="regress",
        estimator_family="ols",
        vcetype="robust",
        has_constant=True,
    )
    original.sample = SampleInfo(
        nobs=50,
        n_input_rows=60,
        sample_mask=[True] * 50 + [False] * 10,
    )
    original.fit = FitInfo(
        df_model=3.0,
        df_resid=46.0,
        rank=4,
        rss=100.0,
        tss=200.0,
        mss=100.0,
        rmse=1.414,
        r2=0.5,
        r2_adj=0.47,
        f_stat=15.0,
        f_pvalue=0.001,
    )
    original.coefficients = [
        CoefficientRow(name="x1", beta=0.5, std_err=0.1, t_stat=5.0, p_value=0.0001, ci_low=0.3, ci_high=0.7),
        CoefficientRow(name="_cons", beta=1.0, std_err=0.2, t_stat=5.0, p_value=0.0001, ci_low=0.6, ci_high=1.4),
    ]
    original.variance = VarianceInfo(
        row_names=["x1", "_cons"],
        values=[[0.01, 0.0], [0.0, 0.04]],
    )
    original.diagnostics = DiagnosticsInfo(
        warnings=["Test warning"],
    )
    original.provenance = ProvenanceInfo(
        source="stata",
        stata_version_target="17",
        stata_command="regress y x1",
    )

    # Serialize
    d = original.to_dict()
    
    # Deserialize
    restored = ResultSchema.from_dict(d)
    
    # Verify
    assert restored.model.command == original.model.command
    assert restored.model.vcetype == original.model.vcetype
    assert restored.sample.nobs == original.sample.nobs
    assert restored.fit.df_model == original.fit.df_model
    assert restored.fit.r2 == original.fit.r2
    assert len(restored.coefficients) == len(original.coefficients)
    assert restored.coefficients[0].name == original.coefficients[0].name
    assert restored.coefficients[0].beta == original.coefficients[0].beta
    assert restored.variance.row_names == original.variance.row_names
    assert restored.provenance.source == original.provenance.source


def test_result_schema_json_round_trip():
    """Test JSON round-trip: ResultSchema -> JSON -> ResultSchema."""
    original = ResultSchema()
    original.model = ModelInfo(command="regress", estimator_family="ols")
    original.sample = SampleInfo(
        nobs=100,
        n_input_rows=100,
        sample_mask=[True] * 100,
    )
    original.coefficients = [
        CoefficientRow(name="x1", beta=2.0),
    ]
    original.variance = VarianceInfo(
        row_names=["x1"],
        values=[[0.01]],
    )

    json_str = original.to_json()
    restored = ResultSchema.from_json(json_str)

    assert restored.model.command == "regress"
    assert restored.sample.nobs == 100
    assert restored.coefficients[0].beta == 2.0
    assert restored.variance.row_names == ["x1"]


def test_result_schema_json_round_trip_preserves_omitted_factor_metadata():
    """JSON round-trip preserves Stata factor base/omitted row flags."""
    original = ResultSchema()
    original.model = ModelInfo(command="regress", estimator_family="ols")
    original.sample = SampleInfo(nobs=10, n_input_rows=10, sample_mask=[True] * 10)
    original.coefficients = [
        CoefficientRow(
            name="1b.g",
            beta=0.0,
            std_err=0.0,
            is_base=True,
            is_omitted=True,
        ),
        CoefficientRow(name="2.g", beta=1.0, std_err=0.2),
    ]
    original.variance = VarianceInfo(
        row_names=["1b.g", "2.g"],
        values=[[0.0, 0.0], [0.0, 0.04]],
    )

    restored = ResultSchema.from_json(original.to_json())

    assert restored.coefficients[0].is_base is True
    assert restored.coefficients[0].is_omitted is True
    assert restored.coefficients[1].is_base is False
    assert restored.coefficients[1].is_omitted is False


def test_result_schema_json_is_valid():
    """Test that to_json produces valid JSON."""
    result = ResultSchema()
    json_str = result.to_json()
    parsed = json.loads(json_str)  # Should not raise
    assert isinstance(parsed, dict)


def _valid_result_dict() -> dict:
    """Return a minimal valid ResultSchema dictionary."""
    return {
        "model": {"command": "regress", "estimator_family": "ols"},
        "sample": {
            "nobs": 3,
            "n_input_rows": 5,
            "sample_mask": [True, True, True, False, False],
        },
        "fit": {"df_model": 2.0, "df_resid": 2.0},
        "coefficients": [
            {"name": "a", "beta": 1.0, "std_err": 0.1, "t_stat": 10.0, "p_value": 0.0},
            {"name": "b", "beta": 2.0, "std_err": 0.2, "t_stat": 10.0, "p_value": 0.0},
        ],
        "variance": {
            "row_names": ["a", "b"],
            "values": [[0.01, 0.0], [0.0, 0.04]],
        },
    }


def test_result_schema_validate():
    """Test that validate() enforces coefficient, VCE, and sample invariants."""
    base = _valid_result_dict()

    # Positive case: valid input passes validation.
    valid = ResultSchema.from_dict(base)
    valid.validate()
    assert len(valid.coefficients) == 2
    assert valid.variance.row_names == ["a", "b"]
    assert valid.sample.nobs == 3

    # Negative cases: each should raise ValueError.
    cases = [
        (
            "coefficients_row_names_length_mismatch",
            lambda d: {
                **d,
                "variance": {"row_names": ["a"], "values": [[0.01]]},
            },
        ),
        (
            "one_by_one_vce_with_two_coefficients",
            lambda d: {
                **d,
                "variance": {"row_names": ["a", "b"], "values": [[0.01]]},
            },
        ),
        (
            "ragged_vce",
            lambda d: {
                **d,
                "variance": {"row_names": ["a", "b"], "values": [[1.0, 0.0], [0.0]]},
            },
        ),
        (
            "coefficient_names_out_of_order",
            lambda d: {
                **d,
                "variance": {"row_names": ["b", "a"], "values": [[0.04, 0.0], [0.0, 0.01]]},
            },
        ),
        (
            "sample_mask_length_mismatch",
            lambda d: {
                **d,
                "sample": {
                    "nobs": 3,
                    "n_input_rows": 5,
                    "sample_mask": [True, True, True, False],
                },
            },
        ),
        (
            "sample_mask_sum_not_nobs",
            lambda d: {
                **d,
                "sample": {
                    "nobs": 3,
                    "n_input_rows": 5,
                    "sample_mask": [True, True, True, True, True],
                },
            },
        ),
    ]

    for label, mutate in cases:
        invalid = mutate(base)
        with pytest.raises(ValueError):
            ResultSchema.from_dict(invalid)


def _capture_display(obj) -> str:
    """Capture the complete display() text of a result or fitted model."""
    buf = io.StringIO()
    with redirect_stdout(buf):
        obj.display()
    return buf.getvalue()


def test_cross_command_display_has_coef_header():
    """Complete display() text of regress, reghdfe, logit, and csdid shares the
    coefficient-table header (ADR-0005)."""
    from stataflow.compat.stata import csdid, logit, regress, reghdfe

    rng = np.random.default_rng(42)
    n = 200
    df = pd.DataFrame({
        "y": rng.normal(size=n),
        "x1": rng.normal(size=n),
        "x2": rng.normal(size=n),
    })
    df["y"] = df["y"] + 0.5 * df["x1"] - 0.3 * df["x2"]

    texts = {"regress": _capture_display(regress(df, y="y", x=["x1", "x2"]))}

    panel = pd.DataFrame({
        "y": rng.normal(size=n),
        "x1": rng.normal(size=n),
        "unit_id": np.repeat(np.arange(40), 5),
        "period": np.tile(np.arange(5), 40),
    })
    texts["reghdfe"] = _capture_display(
        reghdfe(panel, y="y", x=["x1"], absorb=["unit_id", "period"])
    )

    binary = df.copy()
    binary["y_bin"] = (binary["y"] > 0).astype(float)
    texts["logit"] = _capture_display(logit(binary, y="y_bin", x=["x1", "x2"]))

    n_units, n_periods = 50, 5
    units = np.repeat(np.arange(n_units), n_periods)
    times = np.tile(np.arange(n_periods), n_units)
    first_treat = np.repeat(rng.choice([0, 2, 3], size=n_units), n_periods)
    treat = (times >= first_treat).astype(float)
    treat[first_treat == 0] = 0
    did = pd.DataFrame({
        "id": units,
        "time": times,
        "y": 1.0 + 2.0 * treat + rng.normal(size=n_units * n_periods),
        "first_treat": first_treat,
    })
    texts["csdid"] = _capture_display(csdid(did, y="y", id="id", time="time", first_treat="first_treat"))

    for label, text in texts.items():
        assert "Coef." in text, f"{label} display() is missing the coefficient-table header"


def test_summary_avoids_fake_formula_and_inapplicable_r2():
    glm = ResultSchema(
        model=ModelInfo(command="logit", estimator_family="glm"),
        sample=SampleInfo(nobs=20, n_input_rows=20, sample_mask=[True] * 20),
        fit=FitInfo(df_model=1, df_resid=18, pseudo_r2=0.25),
        coefficients=[CoefficientRow(name="income", beta=0.2, std_err=0.1)],
        variance=VarianceInfo(row_names=["income"], values=[[0.01]]),
    )
    did = ResultSchema(
        model=ModelInfo(command="csdid", estimator_family="csdid"),
        sample=SampleInfo(nobs=20, n_input_rows=20, sample_mask=[True] * 20),
        fit=FitInfo(df_model=1, df_resid=18),
        coefficients=[CoefficientRow(name="Tp0", beta=1.0, std_err=0.2)],
        variance=VarianceInfo(row_names=["Tp0"], values=[[0.04]]),
    )

    glm_text = glm.summary()
    did_text = did.summary()

    assert "Terms: income" in glm_text
    assert "y ~" not in glm_text
    assert "Pseudo R2 = 0.2500" in glm_text
    assert "\nR2 =" not in glm_text
    assert "Terms:" not in did_text
    assert "y ~" not in did_text
    assert "\nR2 =" not in did_text
