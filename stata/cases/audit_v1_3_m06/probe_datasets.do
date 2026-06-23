clear all
set more off
foreach d in ships hiv aids hivdata towers uncinate airaccidents lowcount medpar nhanes2 {
    capture noisily webuse `d', clear
    if _rc==0 {
        display "DATASET=" "`d'"
        describe
        summarize
    }
    else {
        display "NOTFOUND=" "`d'"
    }
}
