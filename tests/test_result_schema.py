"""Tests for ResultSchema serialization and deserialization."""

import json
from statapy.results.result import (
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
        sample_mask=[True] * 50,
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
    original.sample = SampleInfo(nobs=100)
    original.coefficients = [
        CoefficientRow(name="x1", beta=2.0),
    ]
    
    json_str = original.to_json()
    restored = ResultSchema.from_json(json_str)
    
    assert restored.model.command == "regress"
    assert restored.sample.nobs == 100
    assert restored.coefficients[0].beta == 2.0


def test_result_schema_json_is_valid():
    """Test that to_json produces valid JSON."""
    result = ResultSchema()
    json_str = result.to_json()
    parsed = json.loads(json_str)  # Should not raise
    assert isinstance(parsed, dict)
