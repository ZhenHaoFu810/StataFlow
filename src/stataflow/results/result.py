"""
Result schema - unified result object schema for Stata-Python comparison.

Defines the shared contract between estimation layer, Stata export layer,
and testing harness.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from typing import Any, Optional


@dataclass
class ModelInfo:
    """Model metadata."""
    command: str = ""
    estimator_family: str = ""
    vcetype: str = "ols"
    weight_type: Optional[str] = None
    fe_vars: list[str] = field(default_factory=list)
    absorb_var: Optional[str] = None
    absorb_vars: list[str] = field(default_factory=list)
    cluster_var: Optional[str | list[str]] = None
    has_constant: bool = True


@dataclass
class SampleInfo:
    """Sample information."""
    nobs: int = 0
    n_input_rows: int = 0
    sample_mask: list[bool] = field(default_factory=list)
    dropped_rows_reason: Optional[list[str]] = None


@dataclass
class FitInfo:
    """Fit statistics."""
    df_model: float = 0.0
    df_resid: float = 0.0
    df_a: Optional[float] = None
    rank: int = 0
    rss: float = 0.0
    tss: float = 0.0
    mss: float = 0.0
    rmse: float = 0.0
    r2: float = 0.0
    r2_adj: float = 0.0
    f_stat: Optional[float] = None
    f_pvalue: Optional[float] = None
    ll: Optional[float] = None
    deviance: Optional[float] = None
    pseudo_r2: Optional[float] = None


@dataclass
class CoefficientRow:
    """Single coefficient row."""
    name: str = ""
    beta: float = 0.0
    std_err: float = 0.0
    t_stat: float = 0.0
    p_value: float = 0.0
    ci_low: float = 0.0
    ci_high: float = 0.0


@dataclass
class VarianceInfo:
    """Variance-covariance matrix."""
    row_names: list[str] = field(default_factory=list)
    values: list[list[float]] = field(default_factory=list)


@dataclass
class DiagnosticsInfo:
    """Diagnostics and warnings."""
    residual_df_correction: Optional[str] = None
    cluster_count: Optional[int] = None
    warnings: list[str] = field(default_factory=list)


@dataclass
class ProvenanceInfo:
    """Source tracking."""
    source: str = "python"  # "python" or "stata"
    stata_version_target: Optional[str] = None
    stata_command: Optional[str] = None


@dataclass
class ResultSchema:
    """
    Unified result object schema.
    
    Top-level structure:
    - model
    - sample
    - fit
    - coefficients
    - variance
    - diagnostics
    - provenance
    """
    model: ModelInfo = field(default_factory=ModelInfo)
    sample: SampleInfo = field(default_factory=SampleInfo)
    fit: FitInfo = field(default_factory=FitInfo)
    coefficients: list[CoefficientRow] = field(default_factory=list)
    variance: VarianceInfo = field(default_factory=VarianceInfo)
    diagnostics: DiagnosticsInfo = field(default_factory=DiagnosticsInfo)
    provenance: ProvenanceInfo = field(default_factory=ProvenanceInfo)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary compatible with schema."""
        return {
            "model": {
                "command": self.model.command,
                "estimator_family": self.model.estimator_family,
                "vcetype": self.model.vcetype,
                "weight_type": self.model.weight_type,
                "fe_vars": self.model.fe_vars,
                "absorb_var": self.model.absorb_var,
                "absorb_vars": self.model.absorb_vars,
                "cluster_var": self.model.cluster_var,
                "has_constant": self.model.has_constant,
            },
            "sample": {
                "nobs": self.sample.nobs,
                "n_input_rows": self.sample.n_input_rows,
                "sample_mask": self.sample.sample_mask,
                "dropped_rows_reason": self.sample.dropped_rows_reason,
            },
            "fit": {
                "df_model": self.fit.df_model,
                "df_resid": self.fit.df_resid,
                "df_a": self.fit.df_a,
                "rank": self.fit.rank,
                "rss": self.fit.rss,
                "tss": self.fit.tss,
                "mss": self.fit.mss,
                "rmse": self.fit.rmse,
                "r2": self.fit.r2,
                "r2_adj": self.fit.r2_adj,
                "f_stat": self.fit.f_stat,
                "f_pvalue": self.fit.f_pvalue,
                "ll": self.fit.ll,
                "deviance": self.fit.deviance,
                "pseudo_r2": self.fit.pseudo_r2,
            },
            "coefficients": [
                {
                    "name": row.name,
                    "beta": row.beta,
                    "std_err": row.std_err,
                    "t_stat": row.t_stat,
                    "p_value": row.p_value,
                    "ci_low": row.ci_low,
                    "ci_high": row.ci_high,
                }
                for row in self.coefficients
            ],
            "variance": {
                "row_names": self.variance.row_names,
                "values": self.variance.values,
            },
            "diagnostics": {
                "residual_df_correction": self.diagnostics.residual_df_correction,
                "cluster_count": self.diagnostics.cluster_count,
                "warnings": self.diagnostics.warnings,
            },
            "provenance": {
                "source": self.provenance.source,
                "stata_version_target": self.provenance.stata_version_target,
                "stata_command": self.provenance.stata_command,
            },
        }

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ResultSchema":
        """Deserialize from dictionary."""
        result = cls()
        
        if "model" in data:
            result.model = ModelInfo(**data["model"])
        if "sample" in data:
            result.sample = SampleInfo(**data["sample"])
        if "fit" in data:
            result.fit = FitInfo(**data["fit"])
        if "coefficients" in data:
            result.coefficients = [
                CoefficientRow(**row) for row in data["coefficients"]
            ]
        if "variance" in data:
            result.variance = VarianceInfo(**data["variance"])
        if "diagnostics" in data:
            result.diagnostics = DiagnosticsInfo(**data["diagnostics"])
        if "provenance" in data:
            result.provenance = ProvenanceInfo(**data["provenance"])
        
        return result

    @classmethod
    def from_json(cls, json_str: str) -> "ResultSchema":
        """Deserialize from JSON string."""
        return cls.from_dict(json.loads(json_str))
