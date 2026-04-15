* Just a quick example of alternative poisson packages

clear all
cls
sysuse auto

gen byte c = 1
bys turn: gen int t = _n
xtset turn t

loc vars price weight gear length

poisson `vars' i.turn, // vce(robust)
* xi: expoisson `vars' i.turn, // vce(robust)
xtpoisson `vars', fe // vce(robust)
glm `vars', family(poisson) link(log)
*ivpoisson gmm `vars' i.turn
*ivpoisson cfunction `vars' i.turn
xi: ppml `vars' i.turn
*ppml_panel_sg `vars', ex(turn) im(c) year(t)
poi2hdfe `vars', id1(turn) id2(c)

