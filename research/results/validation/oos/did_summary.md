# OOS Validation Summary: did

- Cases: 3
- Passed: 2
- Blocked: 1

## Case Results

| case_id | command | dataset | status |
| --- | --- | --- | --- |
| oos_did_imputation_jtrain | `did_imputation` | jtrain | blocked |
| oos_eventstudyinteract_jtrain | `eventstudyinteract` | jtrain | passed |
| oos_csdid_jtrain | `csdid` | jtrain | passed |

## Detail

### oos_did_imputation_jtrain

- Command: `did_imputation`
- Dataset: jtrain
- Status: **blocked**
- Notes: JTRAIN has only 3 time periods (1987-1989), which is insufficient for Stata did_imputation to impute FE for all cohorts. Stata drops to 122 obs and suppresses most coefficients. Python is more lenient. This case documents the behavior difference on short panels.
- Failed fields:
  - nobs: Python=390.000000000000000, Stata=122.000000000000000, abs_diff=2.68e+02, rel_diff=2.20e+00, FAIL
- Failed coefficients:
  - Coefficient 'tau1987' in Stata but not in Python
  - Coefficient 'tau1988' in Stata but not in Python
  - Coefficient 'tau1989' in Stata but not in Python

### oos_eventstudyinteract_jtrain

- Command: `eventstudyinteract`
- Dataset: jtrain
- Status: **passed**

### oos_csdid_jtrain

- Command: `csdid`
- Dataset: jtrain
- Status: **passed**
