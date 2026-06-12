clear all
set more off

foreach command in csdid did_imputation eventstudyinteract {
    capture noisily which `command'
    display "CHECK_`command'_RC=" _rc
}
display "CHECK_DONE"
