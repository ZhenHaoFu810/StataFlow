cls
clear all
use "C:\Git\ppml_hdfe_demo\EXAMPLE_TRADE_FTA_DATA_larger.dta", clear
gegen exporter = group(isoexp)
gegen importer = group(isoimp)
gen double trend = year-1988
cls
keep if category=="TOTAL"
gegen double id1 = group(exporter year)
gegen double id2 = group(importer year)
gegen double id3 = group(exporter importer)
rename trade y 
rename fta x
rename trend z
keep y x z id*

sort id1 id2 id3
compress
save slopes3, replace

ppmlhdfe y x, absorb(id1 id2 id3##c.z) v(1)
