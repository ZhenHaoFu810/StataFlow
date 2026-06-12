"""Stata factor-variable parser and expansion for compat.stata wrappers.

Supported syntax (Phase C subset):
- ``x1`` (bare variable, passed through)
- ``c.x1`` (continuous, passed through as ``x1``)
- ``i.g1`` (categorical indicator, base level omitted)
- ``ib2.g1`` / ``b2.g1`` (categorical indicator with explicit base level)
- ``o2.g1`` (categorical indicator with explicit omitted level)
- ``c.x1#c.x2`` (continuous × continuous interaction)
- ``c.x1##c.x2`` (continuous + continuous + interaction)
- ``i.g1#i.g2`` (categorical × categorical interaction)
- ``i.g1##i.g2`` (categorical main effects + interaction)
- ``i.g1#c.x1`` (categorical × continuous interaction)
- ``i.g1##c.x1`` (categorical main effects + continuous + interaction)
- ``c.x1#i.g1`` / ``c.x1##i.g1`` (mixed interaction, symmetric with ``i.g1#c.x1``)
- ``x1#x2`` / ``x1##x2`` (bare variables inside ``#`` / ``##`` are treated as continuous)
- ``x1#i.g`` / ``x1##i.g`` / ``i.g#x1`` / ``i.g##x1`` (mixed bare/continuous and categorical)
- ``i.g1#i.g2#c.x3`` / ``i.g1##i.g2##c.x3`` (three-way and higher-order interactions)

Explicitly rejected with ``ValueError``:
- ``ib.``, ``b.``, ``o.`` (without level number)
- time-series operators (``L.x``, ``F.x``, etc.)
- any other Stata factor syntax not listed above.
"""

from __future__ import annotations

import re
from typing import List, Tuple, Set, Any

import numpy as np
import pandas as pd

from stataflow.estimators._absorb_spec import AbsorbSpec


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


def _strip_factor_prefix(atom: str) -> str:
    """Return the variable name after stripping c., i., ib#., b#., o#., i(...). prefixes."""
    patterns = [
        r"^ib\d+\.",
        r"^b\d+\.",
        r"^o\d+\.",
        r"^i\([^)]+\)\.",
        r"^[ci]\.",
    ]
    for pat in patterns:
        m = re.match(pat, atom)
        if m:
            return atom[m.end():]
    if "." in atom:
        raise ValueError(f"Invalid factor term atom: {atom}")
    return atom


def get_underlying_vars(term: str) -> list[str]:
    """Extract underlying DataFrame column names from a Stata factor expression.

    Examples
    --------
    - ``i.g`` -> ``['g']``
    - ``c.x`` -> ``['x']``
    - ``i.g##c.x`` -> ``['g', 'x']``
    - ``i.g#i.h`` -> ``['g', 'h']``
    - ``ib2.g`` -> ``['g']``
    - ``i(1 2).g`` -> ``['g']``
    - ``o2.g`` -> ``['g']``
    """
    _reject_unsupported(term)
    parts = re.split(r"(##|#)", term)
    parts = [p for p in parts if p and p not in ("#", "##")]
    seen: set[str] = set()
    out: list[str] = []
    for atom in parts:
        var = _strip_factor_prefix(atom)
        if var not in seen:
            seen.add(var)
            out.append(var)
    return out


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
    if _is_string_like_variable(series):
        raise ValueError(
            f"string variables may not be used as factor variables (Stata r(109)); "
            f"variable '{series.name}' has dtype {series.dtype}"
        )
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


def _is_string_like_variable(series: pd.Series) -> bool:
    """Return True if *series* is a string/object-with-strings/categorical-string variable."""
    dtype = series.dtype
    if pd.api.types.is_string_dtype(dtype):
        return True
    if pd.api.types.is_categorical_dtype(dtype):
        return any(isinstance(cat, str) for cat in series.cat.categories)
    if dtype == object:
        return bool(series.map(lambda v: isinstance(v, str), na_action="ignore").any())
    return False


def _make_dummy(series: pd.Series, level) -> pd.Series:
    """Indicator for ``series == level`` as float."""
    return (series == level).astype(float)


def _expand_single_term(data: pd.DataFrame, term: str, level_source: Optional[pd.DataFrame] = None) -> List[str]:
    """Expand one factor term into new column names added to *data* copy.

    Parameters
    ----------
    data : pd.DataFrame
        DataFrame to which generated columns are added.
    term : str
        Factor term to expand.
    level_source : pd.DataFrame, optional
        DataFrame used to determine factor levels (e.g. screened estimation sample).
        Dummy columns are still written into *data*.

    Returns
    -------
    list[str]
        The list of generated column names in order.
    """
    _reject_unsupported(term)
    src = level_source if level_source is not None else data

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
            # FVAR-002: reject string columns as factor variables (Stata r(109)).
            # For non-string non-numeric columns, explicit base/omitted levels are still
            # rejected because numeric specs cannot be interpreted reliably.
            if (base_spec is not None or omitted_specs) and not pd.api.types.is_numeric_dtype(src[var]):
                if _is_string_like_variable(src[var]):
                    raise ValueError(
                        f"string variables may not be used as factor variables (Stata r(109)); "
                        f"variable '{var}' has dtype {src[var].dtype}"
                    )
                raise ValueError(
                    f"Factor variable '{term}' uses explicit level specification on a "
                    f"non-numeric column '{var}' (dtype={src[var].dtype}). "
                    f"Explicit base/omitted levels (ib#, o#) require numeric variables."
                )
            levels, base, omitted = _levels_for_indicator(src[var], base_spec, omitted_specs)
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
            llevels, lbase, lomitted_set = _levels_for_indicator(src[lvar], lbase_spec, lomitted)
            rlevels, rbase, romitted_set = _levels_for_indicator(src[rvar], rbase_spec, romitted)
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
            levels, base, omitted_set = _levels_for_indicator(src[lvar], lbase_spec, lomitted)
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
            levels, base, omitted_set = _levels_for_indicator(src[rvar], rbase_spec, romitted)
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

    # Multi-way interaction (3+ atoms)
    if len(parts) >= 5:
        # Extract atoms and operators
        atoms = []
        ops = []
        for i, part in enumerate(parts):
            if i % 2 == 0:
                kind, var, base_spec, omitted = _parse_atom(part)
                if kind == "bare":
                    kind = "c"
                atoms.append((kind, var, base_spec, omitted))
            else:
                ops.append(part)
        if not all(op == ops[0] for op in ops):
            raise ValueError("Mixed # and ## operators not supported for >2 way interactions")
        is_double = ops[0] == "##"
        return _expand_multiway_interaction(data, atoms, is_double, level_source=src)

    # Any other structure is unsupported
    raise ValueError(f"Unsupported factor term structure: {term}")


def _interaction_of_atoms(data: pd.DataFrame, atoms: list, level_source: Optional[pd.DataFrame] = None) -> list[str]:
    """Generate interaction columns for a list of atoms (cartesian product of expansions)."""
    from itertools import product
    src = level_source if level_source is not None else data
    atom_cols = []
    for kind, var, base_spec, omitted in atoms:
        if kind in ("c", "bare"):
            if var not in data.columns:
                raise ValueError(f"Variable '{var}' not found in data")
            atom_cols.append([var])
        elif kind == "i":
            levels, base, omitted_set = _levels_for_indicator(src[var], base_spec, omitted)
            nonbase = [ll for ll in levels if ll != base and ll not in omitted_set]
            cols = []
            for lvl in nonbase:
                col_name = f"{_col_name_safe(lvl)}.{var}"
                data[col_name] = _make_dummy(data[var], lvl)
                cols.append(col_name)
            atom_cols.append(cols)
        else:
            raise ValueError(f"Unsupported atom kind in interaction: {kind}")
    
    result = []
    for combo in product(*atom_cols):
        if len(combo) == 1:
            result.append(combo[0])
        else:
            inter_name = "#".join(combo)
            if inter_name not in data.columns:
                data[inter_name] = data[combo[0]].astype(float)
                for c in combo[1:]:
                    data[inter_name] *= data[c].astype(float)
            result.append(inter_name)
    return result


def _expand_multiway_interaction(data: pd.DataFrame, atoms: list, is_double: bool, level_source: Optional[pd.DataFrame] = None) -> list[str]:
    """Expand 3+ way factor interactions."""
    from itertools import combinations
    out_cols: list[str] = []
    for r in range(1, len(atoms) + 1):
        for subset in combinations(atoms, r):
            if is_double or r == len(atoms):
                out_cols.extend(_interaction_of_atoms(data, subset, level_source=level_source))
    return out_cols


def expand_factor_terms(data: pd.DataFrame, terms: List[str], screen_vars: Optional[List[str]] = None) -> Tuple[pd.DataFrame, List[str]]:
    """Expand a list of Stata-style factor terms into concrete DataFrame columns.

    Parameters
    ----------
    data : pd.DataFrame
        Input data.
    terms : list[str]
        Terms such as ``["c.x1##c.x2", "i.g"]``.
    screen_vars : list[str], optional
        If provided, factor levels are determined only from rows where all
        *screen_vars* are non-missing. This aligns base/omitted levels with
        the actual estimation sample.

    Returns
    -------
    expanded_data : pd.DataFrame
        Copy of *data* with generated columns added.
    expanded_terms : list[str]
        Ordered list of concrete column names to use in estimation.
    """
    df = data.copy()
    if screen_vars is not None:
        present = [v for v in screen_vars if v in df.columns]
        if present:
            mask = df[present].notna().all(axis=1)
            df_for_levels = df[mask].copy()
        else:
            df_for_levels = df
    else:
        df_for_levels = df
    out: List[str] = []
    for term in terms:
        out.extend(_expand_single_term(df, term, level_source=df_for_levels))
    return df, out


def _parse_slope_term(term: str) -> AbsorbSpec:
    """Parse a single absorb term that may contain slope syntax.

    Supports:
    - ``firm_id`` → AbsorbSpec(var="firm_id", slopes=[], has_intercept=True)
    - ``firm_id##c.time`` → AbsorbSpec(var="firm_id", slopes=["time"], has_intercept=True)
    - ``firm_id#c.time`` → AbsorbSpec(var="firm_id", slopes=["time"], has_intercept=False)
    - ``firm_id##c.(x1 x2)`` → AbsorbSpec(var="firm_id", slopes=["x1", "x2"], has_intercept=True)
    """
    term = term.strip()

    # Match ##c.(var1 var2) or #c.(var1 var2)
    m = re.match(r"^(.+?)##c\.\(([^)]+)\)$", term)
    if m:
        var = m.group(1).strip()
        slopes = [s.strip() for s in m.group(2).split()]
        return AbsorbSpec(var=var, slopes=slopes, has_intercept=True)

    m = re.match(r"^(.+?)#c\.\(([^)]+)\)$", term)
    if m:
        var = m.group(1).strip()
        slopes = [s.strip() for s in m.group(2).split()]
        return AbsorbSpec(var=var, slopes=slopes, has_intercept=False)

    # Match ##c.var or #c.var
    m = re.match(r"^(.+?)##c\.(.+)$", term)
    if m:
        var = m.group(1).strip()
        slope = m.group(2).strip()
        return AbsorbSpec(var=var, slopes=[slope], has_intercept=True)

    m = re.match(r"^(.+?)#c\.(.+)$", term)
    if m:
        var = m.group(1).strip()
        slope = m.group(2).strip()
        return AbsorbSpec(var=var, slopes=[slope], has_intercept=False)

    # Plain variable (intercept-only)
    return AbsorbSpec(var=term, slopes=[], has_intercept=True)


def _split_absorb_string(value: str) -> List[str]:
    """Split an absorb string on whitespace, but not inside parentheses.

    This ensures ``firm_id##c.(x1 x2)`` stays as a single term.
    """
    terms = []
    current = []
    depth = 0
    for char in value:
        if char == "(":
            depth += 1
            current.append(char)
        elif char == ")":
            depth -= 1
            current.append(char)
        elif char.isspace() and depth == 0:
            if current:
                terms.append("".join(current))
                current = []
        else:
            current.append(char)
    if current:
        terms.append("".join(current))
    return terms


def parse_absorb(value: str | List[str] | tuple) -> List[AbsorbSpec]:
    """Parse ``absorb`` argument allowing string, list, or tuple.

    Supports:
    - Space-separated string: ``"firm year"``
    - List of strings: ``["firm", "year"]``
    - List/tuple with slope syntax: ``[("firm_id", "time_trend")]``
    - List/tuple with multiple slopes: ``[("firm_id", ["x1", "x2"])]``
    - List/tuple with intercept flag: ``[("firm_id", "time_trend", False)]``
    - AbsorbSpec objects (passed through as-is)

    Examples
    --------
    ``parse_absorb("firm year")`` → ``[AbsorbSpec("firm"), AbsorbSpec("year")]``
    ``parse_absorb("firm_id##c.time")`` → ``[AbsorbSpec("firm_id", ["time"])]``
    ``parse_absorb([("firm_id", "time_trend")])`` → ``[AbsorbSpec("firm_id", ["time_trend"])]``
    """
    if isinstance(value, str):
        raw_terms = _split_absorb_string(value)
    else:
        raw_terms = list(value)

    result: List[AbsorbSpec] = []
    for item in raw_terms:
        if isinstance(item, AbsorbSpec):
            result.append(item)
        elif isinstance(item, (list, tuple)):
            # Tuple/list API: (var, slopes..., has_intercept?)
            n = len(item)
            if n == 0:
                raise ValueError("Empty tuple/list in absorb specification")
            var = str(item[0]).strip()
            if n == 1:
                result.append(AbsorbSpec(var=var, slopes=[], has_intercept=True))
            elif n == 2:
                slopes = item[1]
                if isinstance(slopes, str):
                    result.append(AbsorbSpec(var=var, slopes=[slopes], has_intercept=True))
                else:
                    result.append(AbsorbSpec(var=var, slopes=list(slopes), has_intercept=True))
            elif n >= 3:
                slopes = item[1]
                has_intercept = bool(item[2])
                if isinstance(slopes, str):
                    result.append(AbsorbSpec(var=var, slopes=[slopes], has_intercept=has_intercept))
                else:
                    result.append(AbsorbSpec(var=var, slopes=list(slopes), has_intercept=has_intercept))
        else:
            # String term: parse slope syntax
            result.append(_parse_slope_term(str(item).strip()))
    return result
