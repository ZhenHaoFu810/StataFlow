set more off

clear
input byte(y id1 id2)
0 1 1
1 1 1
0 2 1
0 2 2
1 2 2
end

ppmlhdfe y ibn.id1 ibn.id2, noa

ppmlhdfe y, a(id1 id2)


reghdfe y, a(id1 id2)
exit



* noi cscript "ppmlhdfe - extreme case test" adofile ppmlhdfe
set linesize 180

clear
cls
set obs 100
set more off

set seed 12345
gen int id1 = ceil(_n/3)
gen int id2 = ceil(cond(_n==1,_N,_n-1)/3)
gen int y = runiform() < 0.1
li in 1/5
li in `=c(N)-5'/l


// e(ic) is always N / 3
reghdfe y, a(id1 id2)

// this works
reghdfe y, a(id1 id2) prune


// this *eventually* converges after many iterations
ppmlhdfe y, a(id1 id2, prune)
gen byte smpl = e(sample)
keep if smpl
asd


// this doesnt work
ppmlhdfe y, a(id1 id2) accel_skip(1)

asd
