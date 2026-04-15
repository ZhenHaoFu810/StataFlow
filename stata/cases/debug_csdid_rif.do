clear all
set more off
use "D:/OneDrive - SAIF/PhD3/Stata2Python/research/data/public/did/ezunem_prepared.dta", clear
csdid uclms, ivar(city) time(year) gvar(first_treat) method(reg) saverif("D:/OneDrive - SAIF/PhD3/Stata2Python/stata/output/csdid_rif_ezunem", replace)

* Load the RIF file
use "D:/OneDrive - SAIF/PhD3/Stata2Python/stata/output/csdid_rif_ezunem", clear

mata:
rifgt = st_data(., "_g1984_1980_1981 _g1984_1981_1982 _g1984_1982_1983 _g1984_1983_1984 _g1984_1983_1985 _g1984_1983_1986 _g1984_1983_1987 _g1984_1983_1988 _g1985_1980_1981 _g1985_1981_1982 _g1985_1982_1983 _g1985_1983_1984 _g1985_1984_1985 _g1985_1984_1986 _g1985_1984_1987 _g1985_1984_1988")
rifwt = st_data(., "w1984_1981 w1984_1982 w1984_1983 w1984_1984 w1984_1985 w1984_1986 w1984_1987 w1984_1988 w1985_1981 w1985_1982 w1985_1983 w1985_1984 w1985_1985 w1985_1986 w1985_1987 w1985_1988")

* Get rif for Tm3: cols 9 and 2 (g1985_t1982 and g1984_t1981)
* Actually let me check order
cols(rifgt)
ind_gt = (9, 2)
ag_rif = rifgt[.,ind_gt]
ag_wt  = rifwt[.,ind_gt]

mn_attg = mean(ag_rif)
mn_wgt  = mean(ag_wt)
atte    = sum(mn_attg :* mn_wgt) :/ sum(mn_wgt)
wgtw    = (mn_wgt) :/ sum(mn_wgt)
attw    = (mn_attg) :/ sum(mn_wgt)
r1      = (wgtw :* (ag_rif :- mn_attg))
r2      = (attw :* (ag_wt :- mn_wgt))
r3      = (ag_wt :- mn_wgt) :* (atte :/ sum(mn_wgt))
rif_event = rowsum(r1) :+ rowsum(r2) :- rowsum(r3) :+ atte

* Center to get pure IF
if_event = rif_event :- atte

* Simple sum of squares
se_simple = sqrt(sum(if_event:^2))

* Cluster SE by city
cl = st_data(., "city")
ord = order(cl, 1)
ifc = if_event[ord,]
cl2 = cl[ord,]
info = panelsetup(cl2, 1)
ifp = panelsum(ifc, info)
xcros = quadcross(ifp, ifp)
nt = rows(ifc)
se_clust = sqrt(xcros / (nt^2))

"ATE for Tm3:"
atte
"SE simple:"
se_simple
"SE cluster:"
se_clust

* Now compare with just linear combination of IFs (no delta method)
if_lin = (ag_rif[.,1] :- mn_attg[1]) :* (mn_wgt[1]/sum(mn_wgt)) :+ (ag_rif[.,2] :- mn_attg[2]) :* (mn_wgt[2]/sum(mn_wgt))
ifc_lin = if_lin[ord,]
ifp_lin = panelsum(ifc_lin, info)
xcros_lin = quadcross(ifp_lin, ifp_lin)
se_lin = sqrt(xcros_lin / (nt^2))
"SE linear (no delta):"
se_lin

* What are the weights?
"Weights:"
mn_wgt

end
