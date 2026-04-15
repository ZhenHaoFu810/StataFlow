clear all
sysuse auto
reghdfe price weight [aweight = mpg], a(turn) // coef = 4.320956
ivreg2 price weight i.turn [aweight = mpg], partial(i.turn) small // coef = 4.320956
ivreghdfe price weight i.turn [aweight = mpg] // coef = 4.320956

noi cscript "ivreghdfe: ensure resid is correct (issue #61)" adofile ivreghdfe

* Dataset
	sysuse auto
	
	* Spec 1
	ivreghdfe mpg weight (price = headroom), absorb(i.foreign) resid(resid_1)
	
	* Spec 2
	ivreghdfe mpg weight (price = headroom), absorb(i.foreign) resid(resid_2) vce(robust)
	
	* Spec 3 (data must not be ordered by group_id!)
	gen int group_id = (_n <= 35) + 1
	ivreghdfe mpg weight (price = headroom), absorb(i.foreign) resid(resid_3) vce(cluster group_id)

	corr resid_*
	li resid_* in 1/5
	tab group_id


	assert reldif(resid_1, resid_3) < 1e-6
	assert reldif(resid_2, resid_3) < 1e-6

	* Done!

exit
