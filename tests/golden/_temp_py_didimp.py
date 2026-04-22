import pytest
import pandas as pd
from stataflow import DIDImputation

def test_py_didimp_jtrain():
    df = pd.read_stata("research/data/public/did/jtrain_prepared.dta")
    result = DIDImputation(data=df, y="lemploy", id="fcode", time="year", first_treat="first_treat").fit(
        cluster="fcode", allhorizons=True, autosample=True
    )
    for c in result.coefficients:
        print(c.name, c.beta, c.std_err)
    print("nobs:", result.sample.nobs)
