cap ado uninstall ppmlhdfe
net install ppmlhdfe, from("C:/Git/ppml_hdfe_demo/src")
pr drop _all

cls
insheet using "separation_datasets/02.csv", clear comma names double

de
sort y
ppmlhdfe y, keepsing a(id1 id2) sep(relu) v(0) tagsep(sep_relu) zvar(z) r2

tab sep_relu separated, m
assert sep_relu == separated
exit
