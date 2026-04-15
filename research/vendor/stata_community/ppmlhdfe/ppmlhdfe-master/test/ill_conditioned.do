* See:
* - "On the weighting method for least squares problems with linear equality constraints" (G.W. Stewart 1997)
* - https://github.com/sergiocorreia/ppml_hdfe_demo/issues/23
* - https://www.stata.com/manuals13/m-5norm.pdf


cap ado uninstall ppmlhdfe
net install ppmlhdfe, from("C:/Git/ppml_hdfe_demo/src")
pr drop _all


cls
clear
set obs 6
gen y = max(_n -3, 0)
gen double x1 = 100 * (_n<3) + (_n==6) // Also try with higher numbers

ppmlhdfe y x*, sep(simplex)
gen byte sep_simplex = !e(sample)

ppmlhdfe y x*, sep(relu) tagsep(sep_relu) r2 zvar(z)

tab sep_*
assert sep_simplex == sep_relu


exit
