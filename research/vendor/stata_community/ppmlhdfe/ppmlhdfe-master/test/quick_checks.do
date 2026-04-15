* if we drop obs #1, ppml drops x2, not sure why
cls

clear
input double y byte(x1 x2 x3)
  0  2 3 4
  0 -5 0 1
  0  0 2 1
  0  0 0 3
  0 -2 0 1
  0  0 0 2
1.1  1 1 2
 .5  2 2 2
3.3  3 3 2
2.1  4 2 4
end

gen double z = x1 - x2 - x3 + 2 // if y>0
li z x*
reg x1 x2 x3 if y>0
predict resid, resid
li resid x* if y==0

asd

ppml y x*
ppmlhdfe y x*, noa
*ppmlhdfe y x*, noa olsguess
poisson y x*

exit








exit

replace y = exp(rnormal()) * (y>0)

exit
clear
input double y byte(x1 x2 x3)
        0 0 0 1
        0 0 0 1
        0 0 0 2
2.2596662 1 1 2
2.4177196 2 2 2
0.9788354 3 2 1
2.6114680 4 2 1
end

ppmlhdfe, reload
pr drop _all

cls
*replace y = exp(rnormal()) * (y>0)
ppml y x*
ppmlhdfe y x*, noa
*ppmlhdfe y x*, noa olsguess
poisson y x*
exit
glm y x*, fam(poisson) irls ltol(1e-300)
glm y x*, fam(poisson) ml tol(1e-30) nrtol(1e-15)
