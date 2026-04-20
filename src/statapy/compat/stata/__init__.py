"""Stata command compatibility layer for statapy."""

from .linear import regress, xtreg_fe, areg
from .hdfe import reghdfe, ppmlhdfe
from .iv import ivregress_2sls, ivreghdfe
from .glm import logit, probit, poisson
from .did import did_imputation, eventstudyinteract, csdid
from .rdrobust import rdrobust

__all__ = [
    "regress",
    "xtreg_fe",
    "areg",
    "reghdfe",
    "ivregress_2sls",
    "ivreghdfe",
    "logit",
    "probit",
    "poisson",
    "ppmlhdfe",
    "did_imputation",
    "eventstudyinteract",
    "csdid",
    "rdrobust",
]
