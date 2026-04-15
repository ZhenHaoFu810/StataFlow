* ppmlhdfe basic algorithm 

use http://fmwww.bc.edu/RePEc/bocode/e/EXAMPLE_TRADE_FTA_DATA if category=="TOTAL", clear
egen imp = group(isoimp)
egen exp = group(isoexp)
egen pair = group(isoexp isoimp)

local accelerate = 1

local crit 1
local iter 0
local last .
local inner_tol = 1e-4

while (`crit' > 1e-8 | `inner_tol' > `crit') {
	loc ++iter
	di as text _n "Iteration `iter' (crit=`crit') (HDFE tol=`inner_tol')"

	if (`iter'==1) {
		qui su trade, mean
		qui gen double mu = (trade + r(mean)) / 2
		qui gen double eta = log(mu)
		qui gen double z = eta + trade / mu - 1
		qui gen double last_z = z
		qui gen double reg_z = z
	}
	else if (`accelerate') {
		qui replace last_z = z
		qui replace z = eta + trade / mu - 1
		qui replace reg_z = z - last_z + z_resid
		qui replace fta = fta_resid
	}
	else {
		qui replace z = eta + trade / mu - 1
		qui replace reg_z = z
	}
	
	* Tighten HDFE tolerance
	if (`crit' < 10 * `inner_tol') {
		local inner_tol = `inner_tol' / 10
	}
	cap drop *resid

	* Perform HDFE Weighted Least Squares
	qui reghdfe reg_z [aw=mu], ///
	a(imp#year exp#year imp#exp) res(z_resid) keepsing v(-1) ///
	tol(`inner_tol')
	qui reghdfe fta [aw=mu], ///
	a(imp#year exp#year imp#exp) res(fta_resid) keepsing v(-1) ///
	tol(`inner_tol')
	reg z_resid fta_resid [aw=mu], noconstant cluster(pair) nohead
	predict double resid, resid
	
	* Update eta = Xb; mu = exp(eta)
	qui replace eta = z - resid 
	qui replace mu = exp(eta)

	local crit = abs(_b[fta_resid] - `last')
	local last = _b[fta_resid]
}

