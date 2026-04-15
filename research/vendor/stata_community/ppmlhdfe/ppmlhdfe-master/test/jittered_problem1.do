ppmlhdfe ,reload
pr drop _all

cls
clear
input double(y x1 x2 i j)
2 0 0 2 1
0 0 0 4 2
0 0 0 1 1
1 1 0 4 3
0 0 1 2 2
0 0 0 2 2
1 0 0 5 4
0 1 2 2 3
1 0 0 1 1
0 0 0 2 2
0 2 0 1 3
0 0 0 1 3
0 1 0 2 2
0 0 1 5 2
0 0 1 2 4
0 0 0 1 2
0 0 0 1 1
2 0 0 1 2
end

ppmlhdfe y x1 x2, absorb(i j) // works

set seed 1234 // With this seed, it takes 21 iterations
set seed 12345 // With this seed, it takes 164 iterations
set seed 1 // With this seed, it takes 299 iterations

replace y = 1e-7 * (runiform()*100) if y==0
su y
replace y = y / r(min)
su y
ppmlhdfe y x1 x2, absorb(i j) maxiter(30)

exit
