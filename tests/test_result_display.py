"""Tests for command-aware text and HTML result display."""

from __future__ import annotations

import io
from contextlib import redirect_stdout

import pytest

from stataflow.display import build_document
from stataflow.results.result import (
    CoefficientRow,
    DIDInfo,
    DiagnosticsInfo,
    FitInfo,
    IVInfo,
    ModelInfo,
    RDInfo,
    ResultSchema,
    SampleInfo,
    VarianceInfo,
)


def _result(command: str = "regress", family: str = "ols") -> ResultSchema:
    names = ["very_long_predictor_name_that_must_wrap", "_cons"]
    return ResultSchema(
        model=ModelInfo(
            command=command,
            estimator_family=family,
            dependent_variable="outcome",
            regressors=[names[0]],
            estimator_name="Maximum likelihood" if family == "glm" else None,
            vcetype="robust",
            fe_vars=["firm", "year"] if command in {"reghdfe", "ivreghdfe"} else [],
            absorb_vars=["firm", "year"] if command in {"reghdfe", "ivreghdfe"} else [],
            cluster_var="firm",
        ),
        sample=SampleInfo(
            nobs=120,
            n_input_rows=120,
            sample_mask=[True] * 120,
            group_count=24,
        ),
        fit=FitInfo(
            df_model=1,
            df_resid=118,
            rank=2,
            rmse=1.25,
            r2=0.42,
            r2_adj=0.41,
            f_stat=17.5,
            f_pvalue=0.00008,
            ll=-101.25,
            pseudo_r2=0.18,
            deviance=202.5,
            model_test="Wald chi2" if family in {"glm", "ppmlhdfe"} else "F",
            model_stat=17.5,
            model_df_num=1,
            model_df_den=None if family in {"glm", "ppmlhdfe"} else 118,
            model_pvalue=0.00008,
            iterations=6,
            converged=True,
        ),
        coefficients=[
            CoefficientRow(
                name=names[0],
                beta=1.234567,
                std_err=0.123456,
                t_stat=10.0,
                p_value=0.00001,
                ci_low=0.9926,
                ci_high=1.4765,
            ),
            CoefficientRow(
                name="_cons",
                beta=0.5,
                std_err=0.2,
                t_stat=2.5,
                p_value=0.014,
                ci_low=0.104,
                ci_high=0.896,
            ),
        ],
        variance=VarianceInfo(
            row_names=names,
            values=[[0.0152, 0.0], [0.0, 0.04]],
        ),
        diagnostics=DiagnosticsInfo(cluster_count=24),
    )


def test_default_summary_is_full_stata_style_with_confidence_intervals() -> None:
    text = _result().summary()

    assert "Linear regression" in text
    assert "Dependent variable" in text
    assert "outcome" in text
    assert "Number of obs" in text
    assert "[95% conf. interval]" in text
    assert "R-squared" in text
    assert "Prob > F" in text


def test_display_prints_exactly_summary_plus_newline() -> None:
    result = _result()
    stream = io.StringIO()

    with redirect_stdout(stream):
        result.display()

    assert stream.getvalue() == result.summary() + "\n"


def test_summary_preserves_positional_width_and_show_ci_arguments() -> None:
    text = _result().summary(100, False)

    assert "[95% conf. interval]" not in text
    assert max(map(len, text.splitlines())) <= 100


@pytest.mark.parametrize("method", ["summary", "display", "to_html"])
def test_display_api_rejects_unknown_style_and_detail(method: str) -> None:
    result = _result()
    call = getattr(result, method)

    with pytest.raises(ValueError, match="style"):
        call(style="markdown")
    with pytest.raises(ValueError, match="detail"):
        call(detail="verbose")


def test_compact_summary_hides_extended_diagnostics() -> None:
    result = _result("ivregress 2sls", "iv_2sls")
    result.iv = IVInfo(
        estimator="2SLS",
        endogenous=["education"],
        instruments=["experience", "distance"],
        weak_identification_stat=12.4,
        weak_identification_label="Cragg-Donald Wald F",
    )

    full = result.summary()
    compact = result.summary(detail="compact")

    assert "Instrumental variables" in full
    assert "Cragg-Donald Wald F" in full
    assert "Instrumental variables" not in compact
    assert "R-squared" in compact


def test_compact_document_combines_core_fit_statistics_into_one_field() -> None:
    document = build_document(
        _result(),
        style="stata",
        detail="compact",
        show_ci=True,
    )

    assert len(document.fit) == 1
    assert document.fit[0].label == "Model fit"
    assert "R-squared" in document.fit[0].value
    assert "Root MSE" in document.fit[0].value


def test_html_escapes_user_controlled_text_and_uses_same_numbers() -> None:
    result = _result()
    result.model.dependent_variable = "<script>alert(1)</script>"
    result.coefficients[0].name = "<b>x</b>"
    result.variance.row_names[0] = "<b>x</b>"

    html = result.to_html()

    assert "<script>" not in html
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in html
    assert "&lt;b&gt;x&lt;/b&gt;" in html
    assert "1.234567" in html
    assert result._repr_html_() == html


@pytest.mark.parametrize("width", [60, 80, 120])
def test_text_renderer_respects_width_and_wraps_long_names(width: int) -> None:
    text = _result().summary(width=width)

    assert max(map(len, text.splitlines())) <= width
    assert "very_long_predictor_name_that_must_wrap" in text.replace("\n", "")


def test_default_width_keeps_horizontal_coefficient_table() -> None:
    text = _result().summary(width=80)

    assert "Coefficient table" not in text
    assert any("Coef." in line and "Std." in line for line in text.splitlines())


def test_wrapped_coefficient_name_keeps_values_on_its_final_line() -> None:
    text = _result().summary(width=80)
    name_lines = [
        line
        for line in text.splitlines()
        if line.startswith(("very_long_predict", "or_name_that_must", "_wrap"))
    ]

    assert len(name_lines) == 3
    assert all("1.23" not in line for line in name_lines[:-1])
    assert "1.23" in name_lines[-1]


def test_base_and_omitted_rows_use_stata_labels() -> None:
    result = _result()
    result.coefficients[0] = CoefficientRow(
        name="1b.industry",
        is_base=True,
        is_omitted=True,
    )
    result.variance.row_names[0] = "1b.industry"

    text = result.summary()

    assert "(base)" in text
    assert "(omitted)" in text


def test_missing_statistics_render_as_dot_not_zero() -> None:
    result = _result()
    result.coefficients[0].std_err = float("nan")
    result.coefficients[0].t_stat = float("nan")

    row = next(line for line in result.summary().splitlines() if "1.234567" in line)

    assert row.split().count(".") == 2
    assert "nan" not in row.lower()


def test_small_but_readable_fit_statistics_stay_in_decimal_notation() -> None:
    result = _result()
    result.fit.r2_adj = 0.0023

    assert "Adj R-squared = 0.0023" in result.summary()


@pytest.mark.parametrize(
    ("command", "family", "expected", "forbidden"),
    [
        ("regress", "ols", "Linear regression", "Log likelihood"),
        ("xtreg, fe", "fe", "Fixed-effects regression", "Pseudo R2"),
        ("areg", "absorbing_ols", "Absorbed linear regression", "Log likelihood"),
        ("reghdfe", "absorbing_ols", "High-dimensional fixed effects", "Log likelihood"),
        ("ivregress 2sls", "iv_2sls", "Instrumental-variables regression", "Deviance"),
        ("ivreghdfe", "iv_absorbing_ols_2sls", "IV with high-dimensional fixed effects", "Deviance"),
        ("logit", "glm", "Logistic regression", "R-squared"),
        ("probit", "glm", "Probit regression", "R-squared"),
        ("poisson", "glm", "Poisson regression", "R-squared"),
        ("ppmlhdfe", "ppmlhdfe", "Poisson PML with high-dimensional fixed effects", "R-squared"),
        ("did_imputation", "did_imputation", "DID imputation", "R-squared"),
        ("eventstudyinteract", "eventstudyinteract", "Interaction-weighted event study", "R-squared"),
        ("csdid", "csdid", "Callaway-Sant'Anna DID", "R-squared"),
        ("rdrobust", "rdrobust", "Regression discontinuity", "R-squared"),
    ],
)
def test_all_public_commands_use_command_aware_headings(
    command: str,
    family: str,
    expected: str,
    forbidden: str,
) -> None:
    text = _result(command, family).summary()

    assert expected in text
    assert forbidden not in text


def test_iv_did_and_rd_sections_are_command_specific() -> None:
    iv = _result("ivregress 2sls", "iv_2sls")
    iv.iv = IVInfo(
        estimator="2SLS",
        endogenous=["education"],
        instruments=["experience", "distance"],
        excluded_instruments=["distance"],
        underidentification_stat=9.2,
        underidentification_df=1,
        underidentification_pvalue=0.0024,
        weak_identification_stat=18.1,
        weak_identification_label="Cragg-Donald Wald F",
        overidentification_stat=1.4,
        overidentification_df=1,
        overidentification_pvalue=0.24,
        first_stage=[{"name": "education", "partial_r2": 0.21, "f_stat": 18.1}],
    )
    did = _result("csdid", "csdid")
    did.did = DIDInfo(
        aggregation="event",
        id_variable="id",
        time_variable="year",
        cohort_variable="first_treat",
        control_group="not yet treated",
        event_window=[-3, 4],
        pretrend_stat=1.7,
        pretrend_df=3,
        pretrend_pvalue=0.64,
    )
    rd = _result("rdrobust", "rdrobust")
    rd.rd = RDInfo(
        cutoff=0.0,
        running_variable="margin",
        outcome_variable="vote",
        kernel="uniform",
        bwselect="mserd",
        p=1,
        q=2,
        n_left=60,
        n_right=60,
        n_eff_left=45,
        n_eff_right=47,
        h_left=8.1,
        h_right=8.2,
        b_left=12.5,
        b_right=12.7,
    )

    iv_text = iv.summary()
    did_text = did.summary()
    rd_text = rd.summary()

    assert "Endogenous" in iv_text and "First-stage" in iv_text
    assert "Aggregation" in did_text and "Pretrend" in did_text
    assert "Kernel" in rd_text and "uniform" in rd_text
    assert "Effective obs" in rd_text and "Bandwidth h" in rd_text
