# Stata2Python - Phase 0 Bootstrap
"""
A minimal Python package for empirical research in finance and economics.
Targets Stata 17 alignment with verifiable dual-run testing.
"""

__version__ = "0.1.0"

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
