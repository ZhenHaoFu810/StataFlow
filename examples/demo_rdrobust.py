"""Demo: Sharp regression discontinuity (rdrobust)."""

import numpy as np
import pandas as pd
from stataflow.compat.stata import rdrobust

# Synthetic sharp RD design: treatment switches on at the cutoff c = 0.
rng = np.random.default_rng(42)
n = 1000

running = rng.uniform(-1, 1, n)
treat = (running >= 0).astype(float)
y = 0.5 + 0.8 * running + 2.0 * treat + rng.normal(0, 0.5, n)

df = pd.DataFrame({"y": y, "running": running})

result = rdrobust(df, y="y", x="running", c=0.0)

print("rdrobust: sharp RD at cutoff 0 with data-driven bandwidth")
result.display()
