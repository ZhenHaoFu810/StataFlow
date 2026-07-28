"""
Result schema - unified result object schema for Stata-Python comparison.

Defines the shared contract between estimation layer, Stata export layer,
and testing harness.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Optional

import numpy as np


@dataclass
class ModelInfo:
    """Model metadata."""
    command: str = ""
    estimator_family: str = ""
    dependent_variable: Optional[str] = None
    regressors: list[str] = field(default_factory=list)
    estimator_name: Optional[str] = None
    family_metadata: dict[str, Any] = field(default_factory=dict)
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
    group_count: Optional[int] = None


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
    model_test: Optional[str] = None
    model_stat: Optional[float] = None
    model_df_num: Optional[float] = None
    model_df_den: Optional[float] = None
    model_pvalue: Optional[float] = None
    iterations: Optional[int] = None
    converged: Optional[bool] = None


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
    is_base: bool = False
    is_omitted: bool = False


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
    widstat: Optional[float] = None
    idstat: Optional[float] = None
    iddf: Optional[float] = None
    idp: Optional[float] = None
    hansen_j: Optional[float] = None
    hansen_j_df: Optional[float] = None
    hansen_j_pvalue: Optional[float] = None
    warnings: list[str] = field(default_factory=list)


@dataclass
class IVInfo:
    """Instrumental-variable model and diagnostic information."""

    estimator: Optional[str] = None
    endogenous: list[str] = field(default_factory=list)
    instruments: list[str] = field(default_factory=list)
    excluded_instruments: list[str] = field(default_factory=list)
    underidentification_stat: Optional[float] = None
    underidentification_df: Optional[float] = None
    underidentification_pvalue: Optional[float] = None
    weak_identification_stat: Optional[float] = None
    weak_identification_label: Optional[str] = None
    weak_identification_critical_value: Optional[float] = None
    overidentification_stat: Optional[float] = None
    overidentification_df: Optional[float] = None
    overidentification_pvalue: Optional[float] = None
    first_stage: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class DIDInfo:
    """Difference-in-differences display metadata."""

    aggregation: Optional[str] = None
    id_variable: Optional[str] = None
    time_variable: Optional[str] = None
    cohort_variable: Optional[str] = None
    control_group: Optional[str] = None
    event_window: Optional[list[float]] = None
    pretrend_stat: Optional[float] = None
    pretrend_df: Optional[float] = None
    pretrend_pvalue: Optional[float] = None


@dataclass
class RDInfo:
    """Regression-discontinuity display metadata."""

    cutoff: Optional[float] = None
    running_variable: Optional[str] = None
    outcome_variable: Optional[str] = None
    kernel: Optional[str] = None
    bwselect: Optional[str] = None
    p: Optional[int] = None
    q: Optional[int] = None
    n_left: Optional[int] = None
    n_right: Optional[int] = None
    n_eff_left: Optional[int] = None
    n_eff_right: Optional[int] = None
    h_left: Optional[float] = None
    h_right: Optional[float] = None
    b_left: Optional[float] = None
    b_right: Optional[float] = None


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
    iv: IVInfo = field(default_factory=IVInfo)
    did: DIDInfo = field(default_factory=DIDInfo)
    rd: RDInfo = field(default_factory=RDInfo)
    provenance: ProvenanceInfo = field(default_factory=ProvenanceInfo)
    _model: Any = field(default=None, repr=False, compare=False)

    def predict(self, type: str = "xb", newdata=None):
        """Delegate prediction to the underlying fitted model, if available."""
        if self._model is None:
            raise ValueError(
                "predict() is not available for this result. "
                "It may have been deserialized from JSON or the model was not attached."
            )
        return self._model.predict(type=type, newdata=newdata)

    def validate(self) -> None:
        """Validate shape invariants across coefficients, variance matrix, and sample.

        Raises ValueError if dimensions are inconsistent.
        """
        coef_names = [c.name for c in self.coefficients]
        n_coef = len(coef_names)
        v_names = self.variance.row_names
        v_values = self.variance.values

        # Coefficient / VCE dimension alignment.
        # Empty results (e.g., before fitting) skip coefficient/variance checks.
        if n_coef > 0 or len(v_values) > 0:
            if n_coef != len(v_names):
                raise ValueError(
                    f"Shape mismatch: {n_coef} coefficients but "
                    f"{len(v_names)} variance row_names."
                )

            # VCE must be a non-ragged 2-D square matrix.
            if isinstance(v_values, np.ndarray):
                if v_values.ndim != 2 or v_values.shape[0] != v_values.shape[1]:
                    raise ValueError(
                        f"Variance matrix is not a 2-D square matrix: "
                        f"shape {v_values.shape}."
                    )
                if v_values.shape[0] != len(v_names):
                    raise ValueError(
                        f"Variance matrix dimension ({v_values.shape[0]}) does not "
                        f"match row_names length ({len(v_names)})."
                    )
            elif v_values:
                n_v = len(v_values)
                if any(len(row) != n_v for row in v_values):
                    raise ValueError(
                        "Variance matrix rows have non-uniform lengths."
                    )
                if n_v != len(v_names):
                    raise ValueError(
                        f"Variance matrix is not square: "
                        f"{n_v}x{n_v} expected but {len(v_names)} row_names."
                    )

            # Coefficient names must match variance row_names in order.
            if coef_names != v_names:
                raise ValueError(
                    f"Coefficient names do not match variance row_names in order: "
                    f"{coef_names} vs {v_names}."
                )

        # Sample invariants.
        mask = self.sample.sample_mask
        if len(mask) != self.sample.n_input_rows:
            raise ValueError(
                f"Sample mask length ({len(mask)}) does not match n_input_rows "
                f"({self.sample.n_input_rows})."
            )
        if mask and sum(mask) != self.sample.nobs:
            raise ValueError(
                f"Sample mask sum ({sum(mask)}) does not match nobs "
                f"({self.sample.nobs})."
            )

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary compatible with schema."""
        return {
            "model": {
                "command": self.model.command,
                "estimator_family": self.model.estimator_family,
                "dependent_variable": self.model.dependent_variable,
                "regressors": self.model.regressors,
                "estimator_name": self.model.estimator_name,
                "family_metadata": self.model.family_metadata,
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
                "group_count": self.sample.group_count,
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
                "model_test": self.fit.model_test,
                "model_stat": self.fit.model_stat,
                "model_df_num": self.fit.model_df_num,
                "model_df_den": self.fit.model_df_den,
                "model_pvalue": self.fit.model_pvalue,
                "iterations": self.fit.iterations,
                "converged": self.fit.converged,
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
                    "is_base": row.is_base,
                    "is_omitted": row.is_omitted,
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
                "widstat": self.diagnostics.widstat,
                "idstat": self.diagnostics.idstat,
                "iddf": self.diagnostics.iddf,
                "idp": self.diagnostics.idp,
                "hansen_j": self.diagnostics.hansen_j,
                "hansen_j_df": self.diagnostics.hansen_j_df,
                "hansen_j_pvalue": self.diagnostics.hansen_j_pvalue,
                "warnings": self.diagnostics.warnings,
            },
            "iv": {
                "estimator": self.iv.estimator,
                "endogenous": self.iv.endogenous,
                "instruments": self.iv.instruments,
                "excluded_instruments": self.iv.excluded_instruments,
                "underidentification_stat": self.iv.underidentification_stat,
                "underidentification_df": self.iv.underidentification_df,
                "underidentification_pvalue": self.iv.underidentification_pvalue,
                "weak_identification_stat": self.iv.weak_identification_stat,
                "weak_identification_label": self.iv.weak_identification_label,
                "weak_identification_critical_value": (
                    self.iv.weak_identification_critical_value
                ),
                "overidentification_stat": self.iv.overidentification_stat,
                "overidentification_df": self.iv.overidentification_df,
                "overidentification_pvalue": self.iv.overidentification_pvalue,
                "first_stage": self.iv.first_stage,
            },
            "did": {
                "aggregation": self.did.aggregation,
                "id_variable": self.did.id_variable,
                "time_variable": self.did.time_variable,
                "cohort_variable": self.did.cohort_variable,
                "control_group": self.did.control_group,
                "event_window": self.did.event_window,
                "pretrend_stat": self.did.pretrend_stat,
                "pretrend_df": self.did.pretrend_df,
                "pretrend_pvalue": self.did.pretrend_pvalue,
            },
            "rd": {
                "cutoff": self.rd.cutoff,
                "running_variable": self.rd.running_variable,
                "outcome_variable": self.rd.outcome_variable,
                "kernel": self.rd.kernel,
                "bwselect": self.rd.bwselect,
                "p": self.rd.p,
                "q": self.rd.q,
                "n_left": self.rd.n_left,
                "n_right": self.rd.n_right,
                "n_eff_left": self.rd.n_eff_left,
                "n_eff_right": self.rd.n_eff_right,
                "h_left": self.rd.h_left,
                "h_right": self.rd.h_right,
                "b_left": self.rd.b_left,
                "b_right": self.rd.b_right,
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
        if "iv" in data:
            result.iv = IVInfo(**data["iv"])
        if "did" in data:
            result.did = DIDInfo(**data["did"])
        if "rd" in data:
            result.rd = RDInfo(**data["rd"])
        if "provenance" in data:
            result.provenance = ProvenanceInfo(**data["provenance"])

        result.validate()
        return result

    @classmethod
    def from_json(cls, json_str: str) -> "ResultSchema":
        """Deserialize from JSON string."""
        return cls.from_dict(json.loads(json_str))

    # ── Display ────────────────────────────────────────────────────────

    def summary(
        self,
        width: int = 80,
        show_ci: bool = True,
        *,
        style: str = "stata",
        detail: str = "full",
    ) -> str:
        """Return a command-aware Stata-style result table."""
        from stataflow.display import build_document, render_text

        document = build_document(
            self, style=style, detail=detail, show_ci=show_ci
        )
        return render_text(document, width=width)

    def display(
        self,
        width: int = 80,
        show_ci: bool = True,
        *,
        style: str = "stata",
        detail: str = "full",
    ) -> None:
        """Print the command-aware result table to standard output."""
        print(
            self.summary(
                width=width,
                show_ci=show_ci,
                style=style,
                detail=detail,
            )
        )

    def to_html(
        self,
        width: int = 80,
        show_ci: bool = True,
        *,
        style: str = "stata",
        detail: str = "full",
    ) -> str:
        """Return an escaped HTML representation for notebook frontends."""
        from stataflow.display import build_document, render_html

        document = build_document(
            self, style=style, detail=detail, show_ci=show_ci
        )
        return render_html(document)

    def _repr_html_(self) -> str:
        """Return the default rich notebook representation."""
        return self.to_html()

    def __repr__(self) -> str:
        return self.summary()
