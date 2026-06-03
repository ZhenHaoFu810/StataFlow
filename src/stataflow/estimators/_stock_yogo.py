"""
Stock-Yogo (2005) weak instrument critical value tables.

Hard-coded from Stata's s_cdsy() Mata function (ivreg2 Mata library).
Values reproduced by permission per Stata output.

Tables are indexed by:
- model: "2sls" or "liml"
- nendog (K1): number of endogenous regressors
- k2 (L1): number of excluded instruments
- size: 10, 15, 20, or 25 (percent maximal IV size)

For nendog > 1, values are from Stock-Yogo (2005) Tables 5.2-5.3 (2SLS)
and 5.4-5.5 (LIML).
"""

import numpy as np


# 2SLS critical values for 10% maximal IV size
# Rows: nendog (1-10), Cols: k2 (1-10)
_2SLS_10PCT = np.array([
    # k2=1    2      3      4      5      6      7      8      9     10
    [np.nan, 19.93, 22.30, 24.58, 26.87, 29.18, 31.50, 33.84, 36.19, 38.54],  # nendog=1
    [np.nan, 11.59, 12.83, 13.96, 15.09, 16.23, 17.38, 18.54, 19.71, 20.88],  # nendog=2
    [np.nan,  9.54, 10.26, 10.98, 11.72, 12.48, 13.24, 14.01, 14.78, 15.57],  # nendog=3
    [np.nan,  8.75,  9.31,  9.84, 10.38, 10.95, 11.52, 12.10, 12.70, 13.31],  # nendog=4
    [np.nan,  8.25,  8.69,  9.10,  9.52,  9.97, 10.43, 10.90, 11.38, 11.87],  # nendog=5
    [np.nan,  7.91,  8.27,  8.61,  8.96,  9.33,  9.72, 10.12, 10.53, 10.94],  # nendog=6
    [np.nan,  7.65,  7.96,  8.26,  8.57,  8.89,  9.23,  9.58,  9.95, 10.32],  # nendog=7
    [np.nan,  7.45,  7.73,  8.00,  8.27,  8.56,  8.86,  9.17,  9.49,  9.82],  # nendog=8
    [np.nan,  7.28,  7.54,  7.79,  8.04,  8.30,  8.57,  8.86,  9.15,  9.45],  # nendog=9
    [np.nan,  7.15,  7.39,  7.62,  7.85,  8.10,  8.35,  8.62,  8.89,  9.17],  # nendog=10
])

# 2SLS critical values for 15% maximal IV size
_2SLS_15PCT = np.array([
    [np.nan, 11.59, 12.83, 13.96, 15.09, 16.23, 17.38, 18.54, 19.71, 20.88],
    [np.nan,  7.25,  7.80,  8.31,  8.84,  9.38,  9.93, 10.50, 11.07, 11.65],
    [np.nan,  6.17,  6.54,  6.89,  7.25,  7.62,  8.00,  8.39,  8.79,  9.19],
    [np.nan,  5.58,  5.85,  6.11,  6.39,  6.68,  6.98,  7.29,  7.61,  7.93],
    [np.nan,  5.21,  5.43,  5.64,  5.86,  6.09,  6.33,  6.58,  6.83,  7.09],
    [np.nan,  4.96,  5.14,  5.32,  5.51,  5.71,  5.91,  6.12,  6.34,  6.56],
    [np.nan,  4.77,  4.93,  5.09,  5.25,  5.43,  5.61,  5.79,  5.98,  6.17],
    [np.nan,  4.62,  4.77,  4.91,  5.06,  5.22,  5.38,  5.55,  5.72,  5.90],
    [np.nan,  4.51,  4.64,  4.77,  4.91,  5.05,  5.20,  5.36,  5.52,  5.68],
    [np.nan,  4.42,  4.54,  4.66,  4.79,  4.92,  5.06,  5.20,  5.35,  5.50],
])

# 2SLS critical values for 20% maximal IV size
_2SLS_20PCT = np.array([
    [np.nan,  8.75,  9.54, 10.26, 10.98, 11.72, 12.48, 13.24, 14.01, 14.78],
    [np.nan,  5.92,  6.36,  6.75,  7.15,  7.56,  7.98,  8.40,  8.83,  9.27],
    [np.nan,  5.18,  5.47,  5.74,  6.02,  6.31,  6.60,  6.90,  7.21,  7.52],
    [np.nan,  4.77,  5.00,  5.21,  5.43,  5.66,  5.89,  6.12,  6.36,  6.61],
    [np.nan,  4.50,  4.69,  4.86,  5.04,  5.23,  5.42,  5.62,  5.82,  6.03],
    [np.nan,  4.31,  4.47,  4.62,  4.78,  4.95,  5.12,  5.29,  5.47,  5.65],
    [np.nan,  4.17,  4.31,  4.45,  4.59,  4.74,  4.89,  5.05,  5.21,  5.37],
    [np.nan,  4.06,  4.19,  4.31,  4.44,  4.57,  4.71,  4.85,  5.00,  5.14],
    [np.nan,  3.97,  4.09,  4.20,  4.32,  4.44,  4.57,  4.70,  4.83,  4.97],
    [np.nan,  3.90,  4.01,  4.11,  4.22,  4.34,  4.45,  4.58,  4.70,  4.83],
])

# 2SLS critical values for 25% maximal IV size
_2SLS_25PCT = np.array([
    [np.nan,  7.25,  7.80,  8.31,  8.84,  9.38,  9.93, 10.50, 11.07, 11.65],
    [np.nan,  5.22,  5.56,  5.87,  6.19,  6.52,  6.86,  7.20,  7.55,  7.90],
    [np.nan,  4.65,  4.88,  5.10,  5.33,  5.56,  5.80,  6.04,  6.29,  6.54],
    [np.nan,  4.33,  4.51,  4.68,  4.86,  5.04,  5.23,  5.42,  5.62,  5.82],
    [np.nan,  4.11,  4.26,  4.41,  4.56,  4.72,  4.88,  5.05,  5.22,  5.39],
    [np.nan,  3.95,  4.08,  4.21,  4.35,  4.49,  4.63,  4.78,  4.93,  5.08],
    [np.nan,  3.83,  3.95,  4.06,  4.19,  4.31,  4.44,  4.57,  4.71,  4.84],
    [np.nan,  3.74,  3.85,  3.95,  4.07,  4.18,  4.30,  4.42,  4.55,  4.67],
    [np.nan,  3.67,  3.77,  3.86,  3.97,  4.08,  4.19,  4.30,  4.42,  4.54],
    [np.nan,  3.61,  3.70,  3.79,  3.89,  3.99,  4.09,  4.20,  4.31,  4.42],
])

# LIML critical values for 10% maximal IV size
_LIML_10PCT = np.array([
    [16.38,  8.68,  6.46,  5.44,  4.83,  4.43,  4.12,  3.89,  3.71,  3.56],
    [np.nan,  5.33,  4.36,  3.87,  3.56,  3.36,  3.20,  3.08,  2.98,  2.90],
    [np.nan,  4.42,  3.69,  3.30,  3.05,  2.87,  2.73,  2.63,  2.55,  2.49],
    [np.nan,  3.92,  3.32,  2.98,  2.77,  2.61,  2.49,  2.40,  2.33,  2.27],
    [np.nan,  3.60,  3.06,  2.75,  2.56,  2.42,  2.30,  2.22,  2.15,  2.09],
    [np.nan,  3.37,  2.87,  2.58,  2.40,  2.27,  2.16,  2.08,  2.01,  1.95],
    [np.nan,  3.20,  2.73,  2.45,  2.28,  2.15,  2.05,  1.97,  1.90,  1.85],
    [np.nan,  3.07,  2.63,  2.35,  2.19,  2.06,  1.96,  1.88,  1.82,  1.76],
    [np.nan,  2.97,  2.55,  2.28,  2.11,  1.99,  1.89,  1.81,  1.75,  1.70],
    [np.nan,  2.89,  2.49,  2.22,  2.06,  1.93,  1.83,  1.76,  1.70,  1.65],
])

# LIML critical values for 15% maximal IV size
_LIML_15PCT = np.array([
    [ 8.96,  5.33,  4.36,  3.87,  3.56,  3.36,  3.20,  3.08,  2.98,  2.90],
    [np.nan,  3.84,  3.36,  3.09,  2.90,  2.77,  2.67,  2.59,  2.52,  2.46],
    [np.nan,  3.32,  2.95,  2.73,  2.58,  2.47,  2.38,  2.31,  2.25,  2.20],
    [np.nan,  3.01,  2.70,  2.51,  2.37,  2.27,  2.19,  2.12,  2.06,  2.01],
    [np.nan,  2.80,  2.52,  2.35,  2.22,  2.12,  2.05,  1.98,  1.93,  1.88],
    [np.nan,  2.65,  2.39,  2.23,  2.11,  2.02,  1.94,  1.88,  1.83,  1.78],
    [np.nan,  2.54,  2.29,  2.14,  2.03,  1.93,  1.86,  1.80,  1.75,  1.70],
    [np.nan,  2.45,  2.21,  2.07,  1.96,  1.87,  1.80,  1.74,  1.69,  1.64],
    [np.nan,  2.38,  2.15,  2.01,  1.90,  1.82,  1.75,  1.69,  1.64,  1.60],
    [np.nan,  2.32,  2.10,  1.96,  1.86,  1.77,  1.71,  1.65,  1.60,  1.56],
])

# LIML critical values for 20% maximal IV size
_LIML_20PCT = np.array([
    [ 6.66,  4.42,  3.69,  3.30,  3.05,  2.87,  2.73,  2.63,  2.55,  2.49],
    [np.nan,  3.29,  2.89,  2.67,  2.53,  2.43,  2.35,  2.28,  2.23,  2.18],
    [np.nan,  2.89,  2.57,  2.39,  2.27,  2.18,  2.11,  2.05,  2.00,  1.96],
    [np.nan,  2.65,  2.37,  2.21,  2.10,  2.02,  1.95,  1.89,  1.84,  1.80],
    [np.nan,  2.48,  2.23,  2.08,  1.98,  1.90,  1.83,  1.78,  1.73,  1.69],
    [np.nan,  2.36,  2.12,  1.99,  1.89,  1.81,  1.75,  1.70,  1.65,  1.61],
    [np.nan,  2.27,  2.04,  1.91,  1.81,  1.74,  1.68,  1.63,  1.58,  1.54],
    [np.nan,  2.19,  1.98,  1.85,  1.75,  1.68,  1.62,  1.57,  1.53,  1.49],
    [np.nan,  2.13,  1.93,  1.80,  1.71,  1.64,  1.58,  1.53,  1.49,  1.45],
    [np.nan,  2.08,  1.88,  1.76,  1.67,  1.60,  1.54,  1.49,  1.45,  1.41],
])

# LIML critical values for 25% maximal IV size
_LIML_25PCT = np.array([
    [ 5.53,  3.92,  3.32,  2.98,  2.77,  2.61,  2.49,  2.40,  2.33,  2.27],
    [np.nan,  2.92,  2.60,  2.40,  2.27,  2.17,  2.10,  2.04,  1.98,  1.94],
    [np.nan,  2.59,  2.32,  2.16,  2.05,  1.96,  1.90,  1.84,  1.79,  1.75],
    [np.nan,  2.39,  2.15,  2.00,  1.90,  1.82,  1.76,  1.71,  1.66,  1.62],
    [np.nan,  2.24,  2.02,  1.89,  1.79,  1.72,  1.66,  1.61,  1.56,  1.52],
    [np.nan,  2.13,  1.93,  1.80,  1.71,  1.64,  1.58,  1.53,  1.49,  1.45],
    [np.nan,  2.05,  1.86,  1.73,  1.64,  1.57,  1.51,  1.47,  1.42,  1.39],
    [np.nan,  1.99,  1.80,  1.68,  1.59,  1.52,  1.47,  1.42,  1.38,  1.34],
    [np.nan,  1.94,  1.75,  1.64,  1.55,  1.48,  1.43,  1.38,  1.34,  1.30],
    [np.nan,  1.89,  1.71,  1.60,  1.51,  1.45,  1.39,  1.35,  1.31,  1.27],
])

_2SLS_TABLES = {
    10: _2SLS_10PCT,
    15: _2SLS_15PCT,
    20: _2SLS_20PCT,
    25: _2SLS_25PCT,
}

_LIML_TABLES = {
    10: _LIML_10PCT,
    15: _LIML_15PCT,
    20: _LIML_20PCT,
    25: _LIML_25PCT,
}


def stock_yogo_critical_values(
    model: str,
    nendog: int,
    k2: int,
    fuller: float = 0.0,
) -> dict[str, float]:
    """
    Return Stock-Yogo critical values for weak instrument test.

    Parameters
    ----------
    model : str
        "2sls" or "liml".
    nendog : int
        Number of endogenous regressors (K1).
    k2 : int
        Number of excluded instruments (L1).
    fuller : float
        Fuller parameter (only affects LIML). When ``fuller > 0`` with
        ``model="liml"``, the standard LIML critical values are not
        applicable; Fuller-adjusted LIML uses distinct "relative bias"
        and "maximum bias" tables (Stock-Yogo 2005, Tables 5.6–5.9).
        Those tables are not yet hard-coded, so this function returns
        NaN in that case to avoid misleading inference.

    Returns
    -------
    dict with keys "10%", "15%", "20%", "25%".
    """
    model = model.lower()
    if model not in ("2sls", "liml"):
        raise ValueError(f"model='{model}' not supported. Use '2sls' or 'liml'.")

    nendog = int(nendog)
    k2 = int(k2)

    # Fuller-adjusted LIML uses different Stock-Yogo tables (relative bias
    # and maximum bias) that are not yet implemented. Return NaN to avoid
    # returning standard LIML values which would mislead weak-IV diagnosis.
    if model == "liml" and fuller > 0:
        return {"10%": np.nan, "15%": np.nan, "20%": np.nan, "25%": np.nan}

    # When exactly identified (k2 == nendog), 2SLS uses LIML critical values
    use_liml = (model == "2sls" and k2 == nendog)
    tables = _LIML_TABLES if use_liml else (_2SLS_TABLES if model == "2sls" else _LIML_TABLES)
    result = {}
    for pct, table in tables.items():
        if nendog < 1 or nendog > table.shape[0]:
            result[f"{pct}%"] = np.nan
            continue
        if k2 < 1 or k2 > table.shape[1]:
            result[f"{pct}%"] = np.nan
            continue
        val = table[nendog - 1, k2 - 1]
        result[f"{pct}%"] = float(val) if not np.isnan(val) else np.nan
    return result
