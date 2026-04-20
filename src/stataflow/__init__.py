"""
StataFlow (stataflow) 鈥?A Python econometrics toolkit aligned with Stata 17.
Provides a Stata-compatible command layer and native Python estimators,
with field-level dual-run verification.
"""

__version__ = "0.1.3"

# Core estimators (Python-native API)
from .estimators import (
    OLS,
    FixedEffectsOLS,
    AbsorbingOLS,
    IV2SLS,
    IVAbsorbingOLS,
    Logit,
    Probit,
    Poisson,
    PPMLHDFE,
    DIDImputation,
    EventStudyInteract,
    CSDID,
    RDRobust,
)

# Stata compatibility commands
from .compat.stata import (
    regress,
    xtreg_fe,
    areg,
    reghdfe,
    ivregress_2sls,
    ivreghdfe,
    logit,
    probit,
    poisson,
    ppmlhdfe,
    did_imputation,
    eventstudyinteract,
    csdid,
    rdrobust,
)

__all__ = [
    # Core estimators
    "OLS",
    "FixedEffectsOLS",
    "AbsorbingOLS",
    "IV2SLS",
    "IVAbsorbingOLS",
    "Logit",
    "Probit",
    "Poisson",
    "PPMLHDFE",
    "DIDImputation",
    "EventStudyInteract",
    "CSDID",
    "RDRobust",
    # Stata compatibility commands
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
