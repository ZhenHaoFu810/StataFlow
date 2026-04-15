noi cscript "ppmlhdfe - hard3+skew" adofile ppmlhdfe
set linesize 150

clear
input double(y id1 id2)
0 1 1
1 1 1
0 2 1
0 2 2
1 2 2
end

set more off
replace y = 1e-8 in 3
ppmlhdfe y i.id1 i.id2, noa // 18 iterations
ppmlhdfe y, a(id1 id2) // 163 iterations (!), 95,539 subiterations (!)
