* ===========================================================================
* Example: using the iterative rectifier algorithm to detect separation in Tobit models
* ===========================================================================
cls
clear all

* Load SST data (see ppml help file)
use http://personal.lse.ac.uk/tenreyro/mock

* Notice that -tobit- converges to wrong solution
tobit y x z, ll(0)

* ppml help file example
ppml y x z, check
tobit y `e(included)' if e(sample)==1, ll(0)

* replicate the example using -ppmlhdfe-
ppmlhdfe y x z
tobit y x z if e(sample), ll(0)

* we can also use ppmlhdfe's diagnostic tool to detect which variables are driving separation and identify directions-of-recession
ppmlhdfe y x z, tagsep(sep) zvar(z) r2

* Open question to readers: should we add a -check- option equivalent to:
* ppmlhdfe y x*, tagsep(sep) zvar(z) r2
* (in the spirit of ppml's check option)

exit
