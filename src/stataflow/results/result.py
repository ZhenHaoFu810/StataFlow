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

        result.validate()
        return result

    @classmethod
    def from_json(cls, json_str: str) -> "ResultSchema":
        """Deserialize from JSON string."""
        return cls.from_dict(json.loads(json_str))

    # ── Display ────────────────────────────────────────────────────────

    def summary(self, width: int = 80, show_ci: bool = False) -> str:
        """Return a Stata-style regression table as a formatted string.

        Parameters
        ----------
        width : int
            Maximum line width (default 80).
        show_ci : bool
            If True, include 95% confidence interval columns (default False).
        """
        L = []
        sep = "-" * width

        # ── Header ──
        fam = self.model.estimator_family
        cmd = self.model.command or fam
        L.append(f"{cmd}")
        L.append("-" * len(cmd))

        # Model specification line
        coef_names = [c.name for c in self.coefficients]
        x_vars = [n for n in coef_names if n != "_cons"]
        if x_vars:
            x_str = " + ".join(x_vars)
            L.append(f"y ~ {x_str}")

        # Sample and VCE line
        info_parts = [f"N = {self.sample.nobs:,}"]
        vce_label = self.model.vcetype.upper() if self.model.vcetype != "ols" else "OLS"
        info_parts.append(f"VCE = {vce_label}")
        if self.fit.df_a is not None and self.fit.df_a > 0:
            info_parts.append(f"df_a = {int(self.fit.df_a)}")
        if self.model.absorb_vars:
            fe_str = ", ".join(self.model.absorb_vars)
            info_parts.insert(0, f"FE: {fe_str}")
        L.append("    ".join(info_parts))

        if self.model.cluster_var:
            cv = self.model.cluster_var
            cv_str = cv if isinstance(cv, str) else ", ".join(cv)
            L.append(f"Cluster: {cv_str}")

        L.append(sep)

        # ── Coefficient table ──
        if self.coefficients:
            # Determine column widths from actual data
            name_w = max(max(len(c.name) for c in self.coefficients), 6)
            name_w = min(name_w, 18)  # cap very long names

            # GLM families report z-stats, not t-stats
            if fam in ("glm", "ppml", "logit", "probit", "poisson"):
                z_label = "z"
                p_label = "P>|z|"
            else:
                z_label = "t"
                p_label = "P>|t|"
            if show_ci:
                header = (f"{'':>{name_w}}  {'Coef.':>10}  {'Std.Err.':>10}"
                          f"  {z_label:>6}  {p_label:>6}  {'[95% CI]':>20}")
            else:
                header = (f"{'':>{name_w}}  {'Coef.':>10}  {'Std.Err.':>10}"
                          f"  {z_label:>6}  {p_label:>6}")
            L.append(header)
            L.append("-" * len(header))

            for c in self.coefficients:
                beta_str = f"{c.beta:>10.6f}"
                se_str = f"{c.std_err:>10.6f}"
                t_str = f"{c.t_stat:>6.2f}"
                p_str = f"{c.p_value:>6.3f}"
                row = (f"{c.name:>{name_w}}  {beta_str}  {se_str}"
                       f"  {t_str}  {p_str}")
                if show_ci:
                    ci_str = f"[{c.ci_low:.6f}, {c.ci_high:.6f}]"
                    row += f"  {ci_str:>20}"
                L.append(row)

        L.append(sep)

        # ── Footer ──
        fit_stats = []
        if self.fit.r2 is not None:
            fit_stats.append(f"R2 = {self.fit.r2:.4f}")
        if self.fit.r2_adj is not None:
            fit_stats.append(f"R2-Adj = {self.fit.r2_adj:.4f}")
        if self.fit.rmse is not None and self.fit.rmse > 0:
            fit_stats.append(f"RMSE = {self.fit.rmse:.4f}")
        if fit_stats:
            L.append("    ".join(fit_stats))

        # F-statistic (OLS, FE, absorbing_ols)
        if fam in ("ols", "fixed_effects", "absorbing_ols") and self.fit.f_stat is not None:
            L.append(f"F({int(self.fit.df_model)}, {int(self.fit.df_resid)})"
                     f" = {self.fit.f_stat:.2f}"
                     f"    Prob > F = {self.fit.f_pvalue:.4f}")

        # IV-specific: estimator type, Hansen J
        if fam == "iv":
            est_label = self.model.command.upper() if self.model.command else "IV"
            L.append(f"Estimator: {est_label}")

        # GLM-specific: log-likelihood, pseudo-R2, deviance
        if fam in ("glm", "ppml"):
            if self.fit.ll is not None:
                L.append(f"Log-likelihood = {self.fit.ll:.4f}")
            if self.fit.pseudo_r2 is not None:
                L.append(f"Pseudo R2 = {self.fit.pseudo_r2:.4f}")
            if self.fit.deviance is not None:
                L.append(f"Deviance = {self.fit.deviance:.2f}")

        # RD-specific
        if fam == "rdrobust":
            L.append(f"Kernel: {getattr(self.model, 'kernel', 'triangular')}")

        # Warnings
        if self.diagnostics.warnings:
            L.append("")
            L.append("Warnings:")
            for w in self.diagnostics.warnings:
                L.append(f"  * {w}")

        return "\n".join(L)

    def display(self, width: int = 80, show_ci: bool = False) -> None:
        """Print the summary table to stdout."""
        print(self.summary(width=width, show_ci=show_ci))

    def __repr__(self) -> str:
        return self.summary()
