# PPMLHDFE audit fixtures

These CSV files freeze the public Stata example datasets used by the internal
PPMLHDFE dual-run audit:

- `ships.csv`: Stata `webuse ships`, 40 observations.
- `medpar.csv`: Stata `webuse medpar`, 1,495 observations. `provid` is the
  deterministic group code previously generated from `provnum`.

Frozen SHA256 digests:

- `ships.csv`: `39a6a8c7a30844a2c8032a9031065fe4fe6f3d87b38f5cef83280cdd3fff8d66`
- `medpar.csv`: `502cf89b570f95ebc36dcdedc1ad2f7501edf360095cf44f5306980cfe525cc4`

The files were exported without value labels from Stata 17 and are committed so
the audit does not depend on network access. They are validation fixtures and
are excluded from the public package distribution.
