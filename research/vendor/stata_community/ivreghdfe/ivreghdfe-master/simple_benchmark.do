clear all
set more off
timer clear

* Warm-up
sysuse auto
reg price weight
areg price weight, a(turn)
reghdfe price weight, a(turn)
ivreg2 price weight
ivreghdfe price weight, a(turn)

* Benchmark
clear
set obs 10000000
gen double y = runiform()
gen double x1 = runiform()
gen double x2 = runiform()
gen double x3 = runiform()
gen double x4 = runiform()
gen int cl = floor(runiform()*100)
gen int id = floor(runiform()*10000)
gen byte c = 1
cls

* No FEs
timer on 1
reg y x*, cluster(cl)
timer off 1

timer on 2
reghdfe y x*, cluster(cl) noa keepsing
timer off 2

timer on 3
ivreg2 y x*, cluster(cl) small
timer off 3

timer on 4
ivreghdfe y x*, cluster(cl) a(c)
timer off 4

* One set of FEs
timer on 5
areg y x*, cluster(cl) a(id)
timer off 5

timer on 6
reghdfe y x*, cluster(cl) a(id) keepsing
timer off 6

timer on 7
ivreghdfe y x*, cluster(cl) a(id)
timer off 7


timer list
exit
