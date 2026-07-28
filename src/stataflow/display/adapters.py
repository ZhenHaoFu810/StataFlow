"""Command-family adapters for result display."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from stataflow.display.document import (
    DisplayDocument,
    DisplayField,
    DisplaySection,
    DisplayTable,
)
from stataflow.display.formatting import (
    format_bool,
    format_integer,
    format_number,
    format_pvalue,
    is_missing,
)

if TYPE_CHECKING:
    from stataflow.results.result import ResultSchema


_TITLES = {
    "regress": "Linear regression",
    "xtreg, fe": "Fixed-effects regression",
    "xtreg_fe": "Fixed-effects regression",
    "xtreg": "Fixed-effects regression",
    "areg": "Absorbed linear regression",
    "reghdfe": "High-dimensional fixed effects",
    "ivregress 2sls": "Instrumental-variables regression",
    "ivregress_2sls": "Instrumental-variables regression",
    "ivreghdfe": "IV with high-dimensional fixed effects",
    "logit": "Logistic regression",
    "probit": "Probit regression",
    "poisson": "Poisson regression",
    "ppmlhdfe": "Poisson PML with high-dimensional fixed effects",
    "did_imputation": "DID imputation",
    "eventstudyinteract": "Interaction-weighted event study",
    "csdid": "Callaway-Sant'Anna DID",
    "rdrobust": "Regression discontinuity",
}

_LINEAR_FAMILIES = {
    "ols",
    "fe",
    "fixed_effects",
    "absorbing_ols",
    "iv",
    "iv_2sls",
}
_GLM_COMMANDS = {"logit", "probit", "poisson", "ppmlhdfe"}
_DID_COMMANDS = {"did_imputation", "eventstudyinteract", "csdid"}
_RD_COMMANDS = {"rdrobust"}


def _present(value: Any) -> bool:
    return value is not None and value != "" and value != []


def _field(label: str, value: Any) -> DisplayField:
    return DisplayField(label, str(value))


def _command_key(result: ResultSchema) -> str:
    command = result.model.command.strip().lower()
    if command:
        return command
    return result.model.estimator_family.strip().lower()


def _title(result: ResultSchema, command: str) -> str:
    if command in _TITLES:
        return _TITLES[command]
    family = result.model.estimator_family.lower()
    if family.startswith("iv_absorbing_ols"):
        return _TITLES["ivreghdfe"]
    if family.startswith("iv"):
        return _TITLES["ivregress 2sls"]
    return result.model.command or result.model.estimator_family or "Model results"


def _inference_label(result: ResultSchema, command: str) -> str:
    family = result.model.estimator_family.lower()
    if command in _GLM_COMMANDS | _DID_COMMANDS | _RD_COMMANDS:
        return "z"
    if family in {"glm", "ppml", "ppmlhdfe", "csdid", "rd", "rdrobust"}:
        return "z"
    return "t"


def _coefficient_table(result: ResultSchema, command: str, show_ci: bool) -> DisplayTable:
    statistic = _inference_label(result, command)
    headers = ["", "Coef.", "Std. err.", statistic, f"P>|{statistic}|"]
    if show_ci:
        headers.extend(["[95% conf. interval]", ""])
    rows: list[list[str]] = []
    for coefficient in result.coefficients:
        name = coefficient.name
        labels = []
        if coefficient.is_base:
            labels.append("(base)")
        if coefficient.is_omitted:
            labels.append("(omitted)")
        if labels:
            name = f"{name} {' '.join(labels)}"
        row = [
            name,
            format_number(coefficient.beta),
            format_number(coefficient.std_err),
            format_number(coefficient.t_stat, 3),
            format_pvalue(coefficient.p_value),
        ]
        if show_ci:
            row.extend(
                [
                    format_number(coefficient.ci_low),
                    format_number(coefficient.ci_high),
                ]
            )
        rows.append(row)
    return DisplayTable(
        headers=headers,
        rows=rows,
        align=["left"] + ["right"] * (len(headers) - 1),
    )


def _model_test_fields(result: ResultSchema, command: str) -> list[DisplayField]:
    fit = result.fit
    label = fit.model_test
    statistic = fit.model_stat
    pvalue = fit.model_pvalue
    df_num = fit.model_df_num
    df_den = fit.model_df_den
    if not label and fit.f_stat is not None:
        label = "Wald chi2" if command in _GLM_COMMANDS else "F"
        statistic = fit.f_stat
        pvalue = fit.f_pvalue
        df_num = fit.df_model
        df_den = None if command in _GLM_COMMANDS else fit.df_resid
    if not label or is_missing(statistic):
        return []
    if _present(df_num) and _present(df_den):
        statistic_label = f"{label}({format_integer(df_num)}, {format_integer(df_den)})"
    elif _present(df_num):
        statistic_label = f"{label}({format_integer(df_num)})"
    else:
        statistic_label = label
    probability_label = "Prob > F" if label.lower().startswith("f") else "Prob > chi2"
    fields = [_field(statistic_label, format_number(statistic, 2))]
    if not is_missing(pvalue):
        fields.append(_field(probability_label, format_pvalue(pvalue)))
    return fields


def _header_fields(result: ResultSchema) -> list[DisplayField]:
    model = result.model
    fields: list[DisplayField] = []
    if model.dependent_variable:
        fields.append(_field("Dependent variable", model.dependent_variable))
    family = model.estimator_family.lower()
    command = _command_key(result)
    if command not in _DID_COMMANDS | _RD_COMMANDS and family not in _DID_COMMANDS | {"rd", "rdrobust"}:
        regressors = model.regressors or [
            coefficient.name for coefficient in result.coefficients if coefficient.name != "_cons"
        ]
        if regressors:
            fields.append(_field("Terms:", " + ".join(regressors)))
    fields.append(_field("Number of obs", format_integer(result.sample.nobs)))
    if result.sample.group_count is not None:
        fields.append(_field("Number of groups", format_integer(result.sample.group_count)))
    vce = "OLS" if model.vcetype.lower() == "ols" else model.vcetype
    fields.append(_field("VCE", vce))
    if result.diagnostics.cluster_count is not None:
        fields.append(
            _field(
                "Number of clusters",
                format_integer(result.diagnostics.cluster_count),
            )
        )
    fixed_effects = model.absorb_vars or model.fe_vars
    if fixed_effects:
        fields.append(_field("Fixed effects", ", ".join(fixed_effects)))
    if result.fit.df_a is not None:
        fields.append(_field("Absorbed df", format_integer(result.fit.df_a)))
    return fields


def _fit_fields(result: ResultSchema, command: str) -> list[DisplayField]:
    fit = result.fit
    fields = _model_test_fields(result, command)
    family = result.model.estimator_family.lower()
    is_linear = (
        family in _LINEAR_FAMILIES
        or family.startswith("iv_absorbing_ols")
        or command in {"regress", "xtreg, fe", "xtreg_fe", "areg", "reghdfe", "ivregress 2sls", "ivreghdfe"}
    )
    if is_linear:
        if not is_missing(fit.r2):
            fields.append(_field("R-squared", format_number(fit.r2, 4)))
        if not is_missing(fit.r2_adj):
            fields.append(_field("Adj R-squared", format_number(fit.r2_adj, 4)))
        if not is_missing(fit.rmse):
            fields.append(_field("Root MSE", format_number(fit.rmse, 4)))
    elif command in _GLM_COMMANDS or family in {"glm", "ppml", "ppmlhdfe"}:
        if not is_missing(fit.ll):
            fields.append(_field("Log likelihood", format_number(fit.ll, 4)))
        if not is_missing(fit.pseudo_r2):
            fields.append(_field("Pseudo R2", format_number(fit.pseudo_r2, 4)))
        if not is_missing(fit.deviance):
            fields.append(_field("Deviance", format_number(fit.deviance, 4)))
        if fit.iterations is not None:
            fields.append(_field("Iterations", format_integer(fit.iterations)))
        if fit.converged is not None:
            fields.append(_field("Converged", format_bool(fit.converged)))
    return fields


def _iv_section(result: ResultSchema) -> DisplaySection | None:
    iv = result.iv
    diagnostics = result.diagnostics
    fields: list[DisplayField] = []
    if iv.estimator or result.model.estimator_name:
        fields.append(_field("Estimator", iv.estimator or result.model.estimator_name))
    if iv.endogenous:
        fields.append(_field("Endogenous", ", ".join(iv.endogenous)))
    if iv.instruments:
        fields.append(_field("Instruments", ", ".join(iv.instruments)))
    if iv.excluded_instruments:
        fields.append(_field("Excluded instruments", ", ".join(iv.excluded_instruments)))
    idstat = iv.underidentification_stat
    if idstat is None:
        idstat = diagnostics.idstat
    if idstat is not None:
        fields.append(_field("Underidentification statistic", format_number(idstat, 4)))
    idp = iv.underidentification_pvalue
    if idp is None:
        idp = diagnostics.idp
    if idp is not None:
        fields.append(_field("Underidentification p-value", format_pvalue(idp)))
    widstat = iv.weak_identification_stat
    if widstat is None:
        widstat = diagnostics.widstat
    if widstat is not None:
        fields.append(
            _field(
                iv.weak_identification_label or "Weak identification statistic",
                format_number(widstat, 4),
            )
        )
    hansen = iv.overidentification_stat
    if hansen is None:
        hansen = diagnostics.hansen_j
    if hansen is not None:
        fields.append(_field("Hansen J", format_number(hansen, 4)))
    hansen_p = iv.overidentification_pvalue
    if hansen_p is None:
        hansen_p = diagnostics.hansen_j_pvalue
    if hansen_p is not None:
        fields.append(_field("Hansen J p-value", format_pvalue(hansen_p)))

    tables: list[DisplayTable] = []
    if iv.first_stage:
        rows = [
            [
                str(stage.get("name", ".")),
                format_number(stage.get("r2"), 4),
                format_number(stage.get("partial_r2"), 4),
                format_number(stage.get("f_stat"), 4),
            ]
            for stage in iv.first_stage
        ]
        tables.append(
            DisplayTable(
                headers=["First-stage", "R-squared", "Partial R-squared", "F"],
                rows=rows,
                align=["left", "right", "right", "right"],
            )
        )
    if not fields and not tables:
        return None
    return DisplaySection("Instrumental variables", fields, tables)


def _did_section(result: ResultSchema) -> DisplaySection | None:
    did = result.did
    fields: list[DisplayField] = []
    for label, value in (
        ("Aggregation", did.aggregation),
        ("Panel variable", did.id_variable),
        ("Time variable", did.time_variable),
        ("Cohort variable", did.cohort_variable),
        ("Control group", did.control_group),
    ):
        if _present(value):
            fields.append(_field(label, value))
    if did.event_window and len(did.event_window) == 2:
        fields.append(_field("Event window", f"{did.event_window[0]:g} to {did.event_window[1]:g}"))
    if did.pretrend_stat is not None:
        fields.append(_field("Pretrend statistic", format_number(did.pretrend_stat, 4)))
    if did.pretrend_df is not None:
        fields.append(_field("Pretrend df", format_integer(did.pretrend_df)))
    if did.pretrend_pvalue is not None:
        fields.append(_field("Pretrend p-value", format_pvalue(did.pretrend_pvalue)))
    if not fields:
        return None
    return DisplaySection("DID design", fields)


def _rd_section(result: ResultSchema) -> DisplaySection | None:
    rd = result.rd
    fields: list[DisplayField] = []
    for label, value in (
        ("Outcome", rd.outcome_variable),
        ("Running variable", rd.running_variable),
        ("Cutoff", format_number(rd.cutoff) if rd.cutoff is not None else None),
        ("Kernel", rd.kernel),
        ("Bandwidth selection", rd.bwselect),
        ("Polynomial order p/q", f"{rd.p}/{rd.q}" if rd.p is not None and rd.q is not None else None),
    ):
        if _present(value):
            fields.append(_field(label, value))
    tables: list[DisplayTable] = []
    if any(
        value is not None
        for value in (
            rd.n_left,
            rd.n_right,
            rd.n_eff_left,
            rd.n_eff_right,
            rd.h_left,
            rd.h_right,
            rd.b_left,
            rd.b_right,
        )
    ):
        tables.append(
            DisplayTable(
                headers=["", "Left", "Right"],
                rows=[
                    ["Number of obs", format_integer(rd.n_left), format_integer(rd.n_right)],
                    [
                        "Effective obs",
                        format_integer(rd.n_eff_left),
                        format_integer(rd.n_eff_right),
                    ],
                    [
                        "Bandwidth h",
                        format_number(rd.h_left, 4),
                        format_number(rd.h_right, 4),
                    ],
                    [
                        "Bias bandwidth b",
                        format_number(rd.b_left, 4),
                        format_number(rd.b_right, 4),
                    ],
                ],
                align=["left", "right", "right"],
            )
        )
    if not fields and not tables:
        return None
    return DisplaySection("RD design", fields, tables)


def build_document(
    result: ResultSchema,
    *,
    style: str,
    detail: str,
    show_ci: bool,
) -> DisplayDocument:
    """Adapt a result schema into a renderer-neutral display document."""
    if style != "stata":
        raise ValueError("style must be 'stata'")
    if detail not in {"full", "compact"}:
        raise ValueError("detail must be 'full' or 'compact'")

    command = _command_key(result)
    sections: list[DisplaySection] = []
    if detail == "full":
        family = result.model.estimator_family.lower()
        if command in {"ivregress 2sls", "ivregress_2sls", "ivreghdfe"} or family.startswith("iv"):
            section = _iv_section(result)
            if section:
                sections.append(section)
        if command in _DID_COMMANDS or family in _DID_COMMANDS:
            section = _did_section(result)
            if section:
                sections.append(section)
        if command in _RD_COMMANDS or family in {"rd", "rdrobust"}:
            section = _rd_section(result)
            if section:
                sections.append(section)

    fit = _fit_fields(result, command)
    if detail == "compact" and fit:
        fit = [
            DisplayField(
                "Model fit",
                "; ".join(f"{field.label}={field.value}" for field in fit),
            )
        ]

    return DisplayDocument(
        title=_title(result, command),
        command=result.model.command or result.model.estimator_family,
        header=_header_fields(result),
        coefficients=_coefficient_table(result, command, show_ci),
        fit=fit,
        sections=sections,
        warnings=list(result.diagnostics.warnings),
        show_ci=show_ci,
    )
