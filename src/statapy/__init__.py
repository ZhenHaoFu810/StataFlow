# Stata2Python - Phase 0 Bootstrap
"""
A minimal Python package for empirical research in finance and economics.
Targets Stata 17 alignment with verifiable dual-run testing.
"""

__version__ = "0.1.0"

from .estimators import OLS, FixedEffectsOLS, AbsorbingOLS, IV2SLS, IVAbsorbingOLS, Logit, Probit, Poisson, PPMLHDFE, DIDImputation, EventStudyInteract, CSDID

__all__ = ["OLS", "FixedEffectsOLS", "AbsorbingOLS", "IV2SLS", "IVAbsorbingOLS", "Logit", "Probit", "Poisson", "PPMLHDFE", "DIDImputation", "EventStudyInteract", "CSDID"]
