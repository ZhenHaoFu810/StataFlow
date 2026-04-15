* ===========================================================================
* Contingency Table Example from "Likelihood inference in exponential families and directions of recession" (Geyer 2009)
* ===========================================================================
* See page 263; section 2.3

     include common.do

     *import delimited using "http://www.stat.umn.edu/geyer/gdor/catrec.txt", delim(" ") clear
     import delimited using "../input/catrec.txt", delim(" ") clear
     
     * Show certificate of separation Z, and regress it against the Xs
     ppmlhdfe y i.(v*)#i.(v*)#i.(v*) , tagsep(sep) zvar(z) r2
     
     * Code below is just to present a prettier output:
     matrix b = e(b)
     mata: vars = st_matrixcolstripe("b")
     mata: directions = round(st_matrix("b"), 0.001)'
     mata: idx = selectindex(directions)
     mata: (vars, strofreal(directions))[idx, .]

exit
