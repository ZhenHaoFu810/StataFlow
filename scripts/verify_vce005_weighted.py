"""
VCE-005 verification: compare weighted robust/cluster sandwich SEs against Stata 17.

Runs OLS, Logit, Poisson, and PPMLHDFE with analytical weights and robust/cluster VCE,
then compares coefficients and SEs with Stata ground truth.
"""

from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))
sys.path.insert(0, str(PROJECT_ROOT))

from stataflow import OLS, Logit, Poisson, PPMLHDFE, AbsorbingOLS
from tests.golden.test_utils import StataRunner, tolerance_close

np.random.seed(12345)
n = 300
G = 30

x1 = np.random.normal(0, 1, n)
x2 = np.random.normal(0, 1, n)
group = np.random.randint(0, G, n)
unit = np.arange(n)
firm = np.random.randint(0, 60, n)
year = np.random.randint(1990, 2000, n)

# OLS data
w = np.abs(np.random.exponential(scale=1.5, size=n)) + 0.5
eps = np.random.normal(0, 1, n)
y_ols = 1.0 + 0.5 * x1 - 0.3 * x2 + eps

# Logit data
eta_logit = 0.2 + 0.5 * x1 - 0.3 * x2
prob = 1 / (1 + np.exp(-eta_logit))
y_logit = (np.random.random(n) < prob).astype(int)

# Poisson data
eta_pois = 0.1 + 0.3 * x1 - 0.2 * x2
mu_pois = np.exp(eta_pois)
y_pois = np.random.poisson(mu_pois)

# PPMLHDFE data: counts with FE
y_ppml = np.random.poisson(mu_pois * 1.5)

DATA_FILE = PROJECT_ROOT / "stata" / "cases" / "vce005_weighted_data.dta"

df = pd.DataFrame({
    "y_ols": y_ols,
    "y_logit": y_logit,
    "y_pois": y_pois,
    "y_ppml": y_ppml,
    "x1": x1,
    "x2": x2,
    "w": w,
    "group": group,
    "unit": unit,
    "firm": firm,
    "year": year,
})
df.to_stata(str(DATA_FILE), write_index=False)


def run_stata(cmd: str, coefs: list[str]) -> str:
    do_template = f'''
clear all
set more off
use "{DATA_FILE}", clear
{cmd}
'''
    for c in coefs:
        do_template += f'display "B_{c.upper()}=" _b[{c}]\n'
        do_template += f'display "SE_{c.upper()}=" _se[{c}]\n'
    do_template += 'display "VCE005_DONE"\n'
    runner = StataRunner()
    result = runner.run_do_file(do_template, output_dir=str(PROJECT_ROOT / "stata" / "output"))
    if result.exit_code != 0:
        raise RuntimeError(f"Stata failed: {result.error_message}\n{result.output_content}")
    return result.output_content or ""


def parse_stata_log(log: str, coefs: list[str]) -> dict:
    import re
    out = {}
    for c in coefs:
        # Stata may print numbers without leading zero: -.25582393 or .06549958
        num = r"-?\d+\.?\d*|\-?\.\d+"
        m = re.search(rf"B_{c.upper()}\s*=\s*({num})", log)
        out[f"b_{c}"] = float(m.group(1)) if m else None
        m = re.search(rf"SE_{c.upper()}\s*=\s*({num})", log)
        out[f"se_{c}"] = float(m.group(1)) if m else None
    return out


def compare(name: str, py, st: dict, coefs: list[str]) -> None:
    print(f"\n=== {name} ===")
    py_coefs = {c.name: c for c in py.coefficients}
    max_err = 0.0
    for c in coefs:
        py_beta = py_coefs[c].beta
        py_se = py_coefs[c].std_err
        st_beta = st[f"b_{c}"]
        st_se = st[f"se_{c}"]
        ok_b, msg_b = tolerance_close(py_beta, st_beta, name=f"beta[{c}]")
        ok_se, msg_se = tolerance_close(py_se, st_se, name=f"se[{c}]")
        print(f"  {c}: beta py={py_beta:.8f} st={st_beta:.8f} {'OK' if ok_b else 'FAIL'}; "
              f"se py={py_se:.8f} st={st_se:.8f} {'OK' if ok_se else 'FAIL'}")
        if not ok_b:
            print(f"    beta: {msg_b}")
        if not ok_se:
            print(f"    se: {msg_se}")
        max_err = max(max_err, abs(py_se - st_se) / max(abs(st_se), 1e-15))
    print(f"  max relative SE error: {max_err:.3e}")


def main() -> None:
    warnings.filterwarnings("ignore")
    coefs = ["x1", "x2"]

    # OLS weighted robust
    py_ols_r = OLS(data=df, y="y_ols", x=["x1", "x2"], weights=df["w"].values, weight_type="aweight").fit(vce="robust")
    log = run_stata("regress y_ols x1 x2 [aweight=w], vce(robust)", coefs)
    st = parse_stata_log(log, coefs)
    compare("OLS aweight robust", py_ols_r, st, coefs)

    # OLS weighted cluster
    py_ols_c = OLS(data=df, y="y_ols", x=["x1", "x2"], weights=df["w"].values, weight_type="aweight").fit(vce="cluster", cluster="group")
    log = run_stata("regress y_ols x1 x2 [aweight=w], vce(cluster group)", coefs)
    st = parse_stata_log(log, coefs)
    compare("OLS aweight cluster", py_ols_c, st, coefs)

    # Logit weighted robust (Stata logit rejects aweight, use glm)
    py_logit_r = Logit(data=df, y="y_logit", x=["x1", "x2"], weights=df["w"].values).fit(vce="robust")
    log = run_stata("glm y_logit x1 x2 [aweight=w], family(binomial) link(logit) vce(robust)", coefs)
    st = parse_stata_log(log, coefs)
    compare("Logit aweight robust", py_logit_r, st, coefs)

    # Logit weighted cluster
    py_logit_c = Logit(data=df, y="y_logit", x=["x1", "x2"], weights=df["w"].values).fit(vce="cluster", cluster="group")
    log = run_stata("glm y_logit x1 x2 [aweight=w], family(binomial) link(logit) vce(cluster group)", coefs)
    st = parse_stata_log(log, coefs)
    compare("Logit aweight cluster", py_logit_c, st, coefs)

    # Poisson weighted robust (Stata poisson rejects aweight, use glm)
    py_pois_r = Poisson(data=df, y="y_pois", x=["x1", "x2"], weights=df["w"].values).fit(vce="robust")
    log = run_stata("glm y_pois x1 x2 [aweight=w], family(poisson) link(log) vce(robust)", coefs)
    st = parse_stata_log(log, coefs)
    compare("Poisson aweight robust", py_pois_r, st, coefs)

    # Poisson weighted cluster
    py_pois_c = Poisson(data=df, y="y_pois", x=["x1", "x2"], weights=df["w"].values).fit(vce="cluster", cluster="group")
    log = run_stata("glm y_pois x1 x2 [aweight=w], family(poisson) link(log) vce(cluster group)", coefs)
    st = parse_stata_log(log, coefs)
    compare("Poisson aweight cluster", py_pois_c, st, coefs)

    # PPMLHDFE weighted robust (defer: ppmlhdfe aweight syntax needs verification)
    # py_ppml_r = PPMLHDFE(data=df, y="y_ppml", x=["x1", "x2"], absorb="firm", weights=df["w"].values).fit(vce="robust")
    # log = run_stata("ppmlhdfe y_ppml x1 x2, absorb(firm) vce(robust) aweight(w)", coefs)
    # st = parse_stata_log(log, coefs)
    # compare("PPMLHDFE aweight robust", py_ppml_r, st, coefs)

    # PPMLHDFE weighted cluster
    # py_ppml_c = PPMLHDFE(data=df, y="y_ppml", x=["x1", "x2"], absorb="firm", weights=df["w"].values).fit(vce="cluster", cluster="group")
    # log = run_stata("ppmlhdfe y_ppml x1 x2, absorb(firm) vce(cluster group) aweight(w)", coefs)
    # st = parse_stata_log(log, coefs)
    # compare("PPMLHDFE aweight cluster", py_ppml_c, st, coefs)

    # HDFE (reghdfe) weighted robust
    py_hdfe_r = AbsorbingOLS(data=df, y="y_ols", x=["x1", "x2"], absorb="firm", weights=df["w"].values, weight_type="aweight").fit(vce="robust")
    log = run_stata("reghdfe y_ols x1 x2 [aweight=w], absorb(firm) vce(robust)", coefs)
    st = parse_stata_log(log, coefs)
    compare("HDFE aweight robust", py_hdfe_r, st, coefs)

    # HDFE weighted cluster
    py_hdfe_c = AbsorbingOLS(data=df, y="y_ols", x=["x1", "x2"], absorb="firm", weights=df["w"].values, weight_type="aweight").fit(vce="cluster", cluster="group")
    log = run_stata("reghdfe y_ols x1 x2 [aweight=w], absorb(firm) vce(cluster group)", coefs)
    st = parse_stata_log(log, coefs)
    compare("HDFE aweight cluster", py_hdfe_c, st, coefs)


if __name__ == "__main__":
    main()
