clear all
set obs 100
gen y = rnormal()
gen x = rnormal()
gen g1 = mod(_n, 5)
gen g2 = mod(_n, 7)
regress y x, cluster(g1)
regress y x, vce(cluster g1 g2)
