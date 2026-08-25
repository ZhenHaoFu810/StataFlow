"""StataFlow: a Python econometrics toolkit aligned with Stata 17.

The package provides a Stata-compatible command layer and native Python
estimators, with field-level dual-run verification where Stata 17 is available.
"""

__version__ = "1.3.1"

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
