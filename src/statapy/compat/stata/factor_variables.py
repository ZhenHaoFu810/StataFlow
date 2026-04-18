"""Stata factor-variable parser and expansion for compat.stata wrappers.

Supported syntax (Phase C subset):
- ``x1`` (bare variable, passed through)
- ``c.x1`` (continuous, passed through as ``x1``)
- ``i.g1`` (categorical indicator, base level omitted)
- ``ib2.g1`` / ``b2.g1`` (categorical indicator with explicit base level)
- ``o2.g1`` (categorical indicator with explicit omitted level)
- ``c.x1#c.x2`` (continuous × continuous interaction only)
- ``c.x1##c.x2`` (continuous + continuous + interaction)
- ``i.g1#i.g2`` (categorical × categorical interaction only)
- ``i.g1##i.g2`` (categorical main effects + interaction)
- ``i.g1#c.x1`` (categorical × continuous interaction only)
- ``i.g1##c.x1`` (categorical main effects + continuous + interaction)
- ``c.x1#i.g1`` / ``c.x1##i.g1`` (mixed interaction, symmetric with ``i.g1#c.x1``)
- ``x1#x2`` / ``x1##x2`` (bare variables inside ``#`` / ``##`` are treated as continuous)
- ``x1#i.g`` / ``x1##i.g`` / ``i.g#x1`` / ``i.g##x1`` (mixed bare/continuous and categorical)

Explicitly rejected with ``ValueError``:
- ``ib.``, ``b.``, ``o.`` (without level number)
- time-series operators (``L.x``, ``F.x``, etc.)
- three-way or higher-order interactions
- any other Stata factor syntax not listed above.
"""

from __future__ import annotations

import re
from typing import List, Tuple, Set, Any

import numpy as np
import pandas as pd


# Regexes for unsupported syntax that must be hard-rejected
_UNSUPPORTED_PATTERNS = [
    (re.compile(r"\bib\."), "base indicators without level (ib.)"),
    (re.compile(r"\bb\."), "base levels without level (b.)"),
    (re.compile(r"\bo\."), "omitted levels without level (o.)"),
    (re.compile(r"\b[LFDFG12]\d*\."), "time-series operators (L., F., D., etc.)"),
]

# Regex for a simple factor atom: c.var or i.var or bare var
_ATOM_RE = re.compile(r"^(c|i)\.(.+)$")


def _reject_unsupported(term: str) -> None:
    """Raise ValueError if term contains unsupported factor syntax."""
    for pat, desc in _UNSUPPORTED_PATTERNS:
        if pat.search(term):
            raise ValueError(f"Unsupported factor syntax ({desc}) in term: {term}")


def _resolve_level(levels: List[Any], spec: int, dtype=None) -> Any:
    """Resolve a level specification to an actual level value.

    For numeric variables, *spec* is interpreted as an exact value.
    For non-numeric variables, exact match is tried first, then 1-based index fallback.
    """
    # Determine if levels are numeric
    is_numeric = False
    if dtype is not None:
        is_numeric = pd.api.types.is_numeric_dtype(dtype)
    else:
        is_numeric = any(isinstance(lvl, (int, float, np.number)) for lvl in levels)

    # Exact match first
    for lvl in levels:
        try:
            if float(lvl) == float(spec):
                return lvl
        except (ValueError, TypeError):
            if str(lvl) == str(spec):
                return lvl

    if is_numeric:
        raise ValueError(f"Specified level {spec} not found among available levels: {levels}")

    # 1-based index fallback for non-numeric levels
    idx = spec - 1
    if 0 <= idx < len(levels):
        return levels[idx]

    raise ValueError(f"Specified level {spec} not found among available levels: {levels}")


def _parse_atom(atom: str) -> Tuple[str, str, Any, Set[int]]:
    """Parse a single factor atom.

    Returns
    -------
    kind : str
        "c" | "i" | "bare"
    var : str
        Variable name
    base_spec : int or None
        For i-kind, explicit base level specification (e.g. 2 for ib2.g)
    omitted_specs : set[int]
        For i-kind, set of explicitly omitted level specifications
    """
    atom = atom.strip()

    m = re.match(r"^ib(\d+)\.(.+)$", atom)
    if m:
        return "i", m.group(2), int(m.group(1)), set()

    m = re.match(r"^b(\d+)\.(.+)$", atom)
    if m:
        return "i", m.group(2), int(m.group(1)), set()

    m = re.match(r"^o(\d+)\.(.+)$", atom)
    if m:
        return "i", m.group(2), None, {int(m.group(1))}

    m = _ATOM_RE.match(atom)
    if m:
        return m.group(1), m.group(2), None, set()

    if "." in atom:
        raise ValueError(f"Invalid factor term atom: {atom}")

    return "bare", atom, None, set()


def _levels_for_indicator(
    series: pd.Series, base_spec=None, omitted_specs=None
) -> Tuple[List[Any], Any, Set[Any]]:
    """Return sorted unique levels, base level, and omitted levels.

    Parameters
    ----------
    series : pd.Series
    base_spec : int or None
        Explicit base level specification (e.g. 2)
    omitted_specs : set[int] or None
        Explicit omitted level specifications

    Returns
    -------
    levels : list
    base : any
        The base level to omit
    omitted : set
        Additional explicitly omitted levels
    """
    if hasattr(series, "cat") and hasattr(series.cat, "categories"):
        levels = list(series.cat.categories)
    else:
        levels = sorted(series.dropna().unique(), key=lambda v: (str(type(v)), v))

    omitted: Set[Any] = set()
    if omitted_specs:
        for spec in omitted_specs:
            omitted.add(_resolve_level(levels, spec, series.dtype))

    if base_spec is not None:
        base = _resolve_level(levels, base_spec, series.dtype)
    else:
        base = levels[0] if levels else None

    return levels, base, omitted


def _col_name_safe(level) -> str:
    """Create a safe string representation of a level for column naming."""
    return str(level).replace(".", "_")


def _make_dummy(series: pd.Series, level) -> pd.Series:
    """Indicator for ``series == level`` as float."""
    return (series == level).astype(float)


def _expand_single_term(data: pd.DataFrame, term: str) -> List[str]:
    """Expand one factor term into new column names added to *data* copy.

    Returns the list of generated column names in order.
    """
    _reject_unsupported(term)

    # Split on # / ##, keeping delimiters
    parts = re.split(r"(##|#)", term)
    parts = [p for p in parts if p]

    if len(parts) == 1:
        kind, var, base_spec, omitted_specs = _parse_atom(parts[0])
        if kind in ("c", "bare"):
            # No expansion needed; just use the variable name
            if var not in data.columns:
                raise ValueError(f"Variable '{var}' not found in data")
            return [var]
        elif kind == "i":
            levels, base, omitted = _levels_for_indicator(data[var], base_spec, omitted_specs)
            if len(levels) <= 1:
                # No variation to model
                return []
            out_cols = []
            for lvl in levels:
                if lvl == base or lvl in omitted:
                    continue
                col_name = f"{_col_name_safe(lvl)}.{var}"
                data[col_name] = _make_dummy(data[var], lvl)
                out_cols.append(col_name)
            return out_cols

    if len(parts) == 3 and parts[1] in ("#", "##"):
        left, op, right = parts
        lkind, lvar, lbase_spec, lomitted = _parse_atom(left)
        rkind, rvar, rbase_spec, romitted = _parse_atom(right)

        is_double = op == "##"

        # Inside # / ##, bare variables are treated as continuous (c.)
        if lkind == "bare":
            lkind = "c"
        if rkind == "bare":
            rkind = "c"

        # Validate allowed combinations for Phase C
        allowed_pairs = {
            ("c", "c"),
            ("i", "i"),
            ("i", "c"),
            ("c", "i"),
        }
        if (lkind, rkind) not in allowed_pairs:
            raise ValueError(f"Unsupported factor interaction: {term}")

        out_cols: List[str] = []

        if lkind == "c" and rkind == "c":
            # c.x1 #/## c.x2
            if lvar not in data.columns or rvar not in data.columns:
                raise ValueError(f"Variables not found in data for term: {term}")
            inter_col = f"c.{lvar}#c.{rvar}"
            data[inter_col] = data[lvar].astype(float) * data[rvar].astype(float)
            if is_double:
                out_cols = [lvar, rvar, inter_col]
            else:
                out_cols = [inter_col]
            return out_cols

        if lkind == "i" and rkind == "i":
            # i.g1 #/## i.g2
            llevels, lbase, lomitted_set = _levels_for_indicator(data[lvar], lbase_spec, lomitted)
            rlevels, rbase, romitted_set = _levels_for_indicator(data[rvar], rbase_spec, romitted)
            lnonbase = [ll for ll in llevels if ll != lbase and ll not in lomitted_set]
            rnonbase = [rl for rl in rlevels if rl != rbase and rl not in romitted_set]
            if len(lnonbase) == 0 or len(rnonbase) == 0:
                # If either has no non-base/non-omitted levels, interaction is empty
                pass
            else:
                for ll in lnonbase:
                    ll_col = f"{_col_name_safe(ll)}.{lvar}"
                    data[ll_col] = _make_dummy(data[lvar], ll)
                for rl in rnonbase:
                    rl_col = f"{_col_name_safe(rl)}.{rvar}"
                    data[rl_col] = _make_dummy(data[rvar], rl)
                for ll in lnonbase:
                    for rl in rnonbase:
                        inter_col = f"{_col_name_safe(ll)}.{lvar}#{_col_name_safe(rl)}.{rvar}"
                        data[inter_col] = (
                            _make_dummy(data[lvar], ll) * _make_dummy(data[rvar], rl)
                        )
                        out_cols.append(inter_col)
                if is_double:
                    left_cols = [f"{_col_name_safe(ll)}.{lvar}" for ll in lnonbase]
                    right_cols = [f"{_col_name_safe(rl)}.{rvar}" for rl in rnonbase]
                    out_cols = left_cols + right_cols + out_cols
            return out_cols

        if lkind == "i" and rkind == "c":
            # i.g1 #/## c.x
            levels, base, omitted_set = _levels_for_indicator(data[lvar], lbase_spec, lomitted)
            nonbase = [lvl for lvl in levels if lvl != base and lvl not in omitted_set]
            if len(nonbase) > 0:
                for lvl in nonbase:
                    dummy_col = f"{_col_name_safe(lvl)}.{lvar}"
                    data[dummy_col] = _make_dummy(data[lvar], lvl)
                    inter_col = f"{_col_name_safe(lvl)}.{lvar}#c.{rvar}"
                    data[inter_col] = data[dummy_col] * data[rvar].astype(float)
                    out_cols.append(inter_col)
                if is_double:
                    main_cols = [f"{_col_name_safe(lvl)}.{lvar}" for lvl in nonbase]
                    out_cols = main_cols + [rvar] + out_cols
            else:
                if is_double:
                    out_cols = [rvar]
            return out_cols

        if lkind == "c" and rkind == "i":
            # c.x #/## i.g  (symmetric with i.g #/## c.x)
            levels, base, omitted_set = _levels_for_indicator(data[rvar], rbase_spec, romitted)
            nonbase = [lvl for lvl in levels if lvl != base and lvl not in omitted_set]
            if len(nonbase) > 0:
                for lvl in nonbase:
                    dummy_col = f"{_col_name_safe(lvl)}.{rvar}"
                    data[dummy_col] = _make_dummy(data[rvar], lvl)
                    inter_col = f"{_col_name_safe(lvl)}.{rvar}#c.{lvar}"
                    data[inter_col] = data[dummy_col] * data[lvar].astype(float)
                    out_cols.append(inter_col)
                if is_double:
                    main_cols = [f"{_col_name_safe(lvl)}.{rvar}" for lvl in nonbase]
                    out_cols = main_cols + [lvar] + out_cols
            else:
                if is_double:
                    out_cols = [lvar]
            return out_cols

    # Any other structure is unsupported
    raise ValueError(f"Unsupported factor term structure: {term}")


def expand_factor_terms(data: pd.DataFrame, terms: List[str]) -> Tuple[pd.DataFrame, List[str]]:
    """Expand a list of Stata-style factor terms into concrete DataFrame columns.

    Parameters
    ----------
    data : pd.DataFrame
        Input data.
    terms : list[str]
        Terms such as ``["c.x1##c.x2", "i.g"]``.

    Returns
    -------
    expanded_data : pd.DataFrame
        Copy of *data* with generated columns added.
    expanded_terms : list[str]
        Ordered list of concrete column names to use in estimation.
    """
    df = data.copy()
    out: List[str] = []
    for term in terms:
        out.extend(_expand_single_term(df, term))
    return df, out


def parse_absorb(value: str | List[str]) -> List[str]:
    """Parse ``absorb`` argument allowing list or space-separated string.

    Examples
    --------
    ``parse_absorb("firm year")`` → ``["firm", "year"]``
    ``parse_absorb(["firm", "year"])`` → ``["firm", "year"]``
    """
    if isinstance(value, str):
        return value.split()
    return [str(v) for v in value]
