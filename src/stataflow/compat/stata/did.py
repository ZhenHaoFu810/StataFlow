"""Stata DID command wrappers."""

from __future__ import annotations

from typing import Optional

from stataflow.estimators import DIDImputation, EventStudyInteract, CSDID


def did_imputation(
    data,
    y: str,
    id: str,
    time: str,
    first_treat: str,
    *,
    cluster: Optional[str] = None,
    allhorizons: bool = False,
    autosample: bool = False,
    window: Optional[list[int]] = None,
    minn: Optional[int] = None,
    controls: Optional[list[str]] = None,
    unitcontrols: Optional[list[str]] = None,
    timecontrols: Optional[list[str]] = None,
    pretrends: int = 0,
    wtr: Optional[list[str]] = None,
    hetby: Optional[str] = None,
    saveestimates: Optional[str] = None,
    saveweights: bool = False,
    sum: bool = False,
    **kwargs,
) -> object:
    """
    Stata-compatible wrapper for ``did_imputation``.

    Maps to :class:`stataflow.estimators.DIDImputation`.
    """
    if kwargs:
        raise ValueError(f"Unsupported arguments: {list(kwargs.keys())}")

    model = DIDImputation(
        data=data,
        y=y,
        id=id,
        time=time,
        first_treat=first_treat,
    )
    return model.fit(
        cluster=cluster,
        allhorizons=allhorizons,
        autosample=autosample,
        window=window,
        minn=minn,
        controls=controls,
        unitcontrols=unitcontrols,
        timecontrols=timecontrols,
        pretrends=pretrends,
        wtr=wtr,
        hetby=hetby,
        saveestimates=saveestimates,
        saveweights=saveweights,
        sum=sum,
    )


def eventstudyinteract(
    data,
    y: str,
    *,
    cohort: str,
    control_cohort: str,
    absorb: list[str],
    event_dummies: Optional[list[str]] = None,
    time: Optional[str] = None,
    first_treat: Optional[str] = None,
    horizons: Optional[list[int]] = None,
    omit: Optional[int] = None,
    vce: str = "ols",
    cluster: Optional[str] = None,
    **kwargs,
) -> object:
    """
    Stata-compatible wrapper for ``eventstudyinteract``.

    Maps to :class:`stataflow.estimators.EventStudyInteract`.

    Parameters
    ----------
    event_dummies : list[str], optional
        Pre-generated relative-time dummy variable names. If provided,
        ``time``, ``first_treat``, and ``horizons`` are ignored.
    time, first_treat, horizons, omit
        Alternative auto-generation mode. The wrapper creates dummy
        variables ``Dm{h}`` (for ``h < 0``), ``D0``, or ``Dp{h}``
        (for ``h > 0``) on a copy of ``data``. The horizon ``omit``
        is excluded as the reference category.
    """
    if kwargs:
        raise ValueError(f"Unsupported arguments: {list(kwargs.keys())}")

    df = data.copy()

    if event_dummies is not None:
        used_event_dummies = list(event_dummies)
    else:
        if time is None or first_treat is None or horizons is None:
            raise ValueError(
                "Either event_dummies or (time, first_treat, horizons) must be provided."
            )
        if omit is not None and omit not in horizons:
            raise ValueError("omit must be one of the horizons.")

        used_event_dummies = []
        rel_time = df[time] - df[first_treat]
        rel_time = rel_time.where(df[first_treat] > 0, -1000)

        for h in horizons:
            if h == omit:
                continue
            if h < 0:
                col = f"Dm{abs(h)}"
            elif h == 0:
                col = "D0"
            else:
                col = f"Dp{h}"
            df[col] = (rel_time == h).astype(float)
            used_event_dummies.append(col)

    model = EventStudyInteract(
        data=df,
        y=y,
        event_dummies=used_event_dummies,
        cohort=cohort,
        control_cohort=control_cohort,
        absorb=absorb,
    )
    return model.fit(vce=vce, cluster=cluster)


def csdid(
    data,
    y: str,
    id: str,
    time: str,
    first_treat: str,
    *,
    method: str = "reg",
    vce: Optional[str] = None,
    cluster: Optional[str] = None,
    xvars: Optional[list[str]] = None,
    aggtype: Optional[str] = None,
    **kwargs,
) -> object:
    """
    Stata-compatible wrapper for ``csdid``.

    Maps to :class:`stataflow.estimators.CSDID`.
    """
    if kwargs:
        raise ValueError(f"Unsupported arguments: {list(kwargs.keys())}")

    model = CSDID(
        data=data,
        y=y,
        id=id,
        time=time,
        first_treat=first_treat,
        xvars=xvars,
    )
    model.fit(method=method, vce=vce, cluster=cluster)
    if aggtype is None:
        aggtype = "event"
    return model.estat(aggtype=aggtype)
