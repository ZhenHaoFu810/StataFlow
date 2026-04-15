{smcl}
{* *! version 0.0  2apr2020}{...}
{viewerjumpto "Syntax" "eventstudyinteract##syntax"}{...}
{viewerjumpto "Description" "eventstudyinteract##description"}{...}
{viewerjumpto "Options" "eventstudyinteract##options"}{...}
{viewerjumpto "Examples" "eventstudyinteract##examples"}{...}
{viewerjumpto "Saved results" "eventstudyinteract##saved_results"}{...}
{viewerjumpto "Author" "eventstudyinteract##author"}{...}
{viewerjumpto "Acknowledgements" "eventstudyinteract##acknowledgements"}{...}
{title:Title}

{p2colset 5 19 21 2}{...}
{p2col :{hi:eventstudyinteract} {hline 2}}
implements the interaction weighted (IW) estimator and constructs pointwise confidence interval for the estimation of dynamic treatment effects. 
To estimate the dynamic effects of an absorbing treatment, researchers often use two-way fixed effects (TWFE) regressions that include leads and lags of the treatment (event study specification). 
Units are categorized into different cohorts based on their initial treatment timing.  
Sun and Abraham (2020) proposes this estimator as an alternative to the TWFE regression in the presence of treatment effects heterogeneous across cohorts. 
Under treatment effects heterogeneity, the TWFE regression can result in estimates with uninterpretable weights, which can be assessed by the Stata module {helpb eventstudyweights}.
The IW estimator is implemented in three steps.  
First, estimate the interacted regression with {helpb reghdfe}, where the interactions are between relative time indicators and cohort indicators.
Second, estimate the cohort shares underlying each relative time.  
Third, take the weighted average of estimates from the first step, with weights set to the estimated cohort shares.
{p_end}
{p2colreset}{...}
 
{marker syntax}{title:Syntax}

{p 8 15 2}
{cmd:eventstudyinteract}
{y} {rel_time_list} {ifin}
{weight} {cmd:,} {opth absorb:(reghdfe##absvar:absvars)} {opth cohort:(eventstudyinteract##cohort:variable)}
            {opth control_cohort:(eventstudyinteract##cohort:variable)} 
 [{it:options} {opth covariates:(eventstudyinteract##cohort:varlist)}]
 
{pstd}
where {it:rel_time_list} is the list of relative time indicators as you would have included in the canonical two-way fixed effects regression, e.g.,
{p_end} 
		{it:rel_time_1} [{it:rel_time_2} [...]] 
		
{pstd} See {help eventstudyinteract##examples:illustration} for an example of generating these relative time indicators. 
The relative time indicators should take the value of zero for never treated units.  {p_end} 

{pstd}
Users should shape their dataset to a long format where each observation is at the unit-time level. 
See {help eventstudyinteract##examples:illustration} for an example of specifying the syntax.
The syntax is similar to {helpb reghdfe} in specifying fixed effects (with {help reghdfe##opt_absorb:absorb}) 
and the type of standard error reported (with {help reghdfe##opt_vce:vcetype}).  
Regressors other than the relative time indicators need to be specified separately in {opth covariates(varlist)}.
Furthermore, it also requires the user to specify the cohort categories as well as which cohort is the control cohort (see {help eventstudyinteract##by_notes:important notes below}).  
Note that Sun and Abraham (2020) only establishes the validity of the IW estimators for balanced panel data without covariates. {opt eventstudyinteract} does not impose a balanced panel by dropping units with observations that are missing in any time period.  Instead, it evaluates the IW estimators for unbalanced panel data by estimating the interacted regression using all observations.  

{pstd}
{opt eventstudyinteract} requires {helpb avar} (Baum and Schaffer, 2013) and {helpb reghdfe} (Sergio, 2017) to be installed.
Installation of {opt eventstudyinteract} will install {helpb avar} and {helpb reghdfe} (and its dependencies) from ssc if necessary. {p_end}

{synopthdr :options}
{synoptline}
{syntab :Must specify}
{marker cohort}{...}
{synopt :{opth cohort(varname)}}categorical variable that corresponds to the initial treatment timing of each unit.
If there are units that receive multiple treatments, Sun and Abraham (2020) defines the initial treatment timing to be based on the first treatment.
This categorical variable should be set to be missing for never treated units.{p_end}
{synopt :{opth control_cohort(varname)}}binary variable that corresponds to the control cohort, which can be never-treated units or last-treated units.
If using last-treated unit as control cohort, exclude the time periods when the last cohort receives treatment. {p_end}
{synopt :{opth absorb(varlist)}}specifies unit and time fixed effects.{p_end}

{syntab :Optional}
{synopt :{opth covariates(varlist)}}specify covariates that lend validity to the parallel trends assumption, i.e. covariates you would have included in the canonical two-way fixed effects regressions. {p_end}

{syntab :VCE}
{synopt :{opt vce}{cmd:(}{help reghdfe##opt_vce:vcetype} [{cmd:,}{it:opt}]{cmd:)}}{it:vcetype}
may be {opt un:adjusted} (default), {opt r:obust} or {opt cl:uster} {help fvvarlist} (allowing two- and multi-way clustering){p_end}
{synopt :}suboptions {opt bw(#)}, {opt ker:nel(str)}, {opt dkraay(#)} and {opt kiefer} allow for AC/HAC estimates; see the {help avar} package{p_end}

{syntab :Saved Output}
{pstd}
{opt eventstudyinteract} reports the IW estimates in {cmd:e(b_iw)} and standard error in {cmd:e(V_iw)}.  
Since the interacted regression is performed by {helpb reghdfe}, {cmd:e(b)}  keeps all results from  {helpb reghdfe} 
(unlabeled at the moment other than covariates, which can be accessed via {cmd:_b[covariates]} and {cmd:_se[covariates]}). Stata's post-estimation commands such as {helpb test} look for coefficients and variance covariance matrix stored in {cmd:e(b)} 
and {cmd:e(V)}. To use these commands on the IW estimates only, a workaround is to run the following before Stata's post-estimation commands: {p_end}
{phang2}. {stata matrix b = e(b_iw)}{p_end}
{phang2}. {stata matrix V = e(V_iw)}{p_end}
{phang2}. {stata ereturn post b V}{p_end}
{pstd}Additionally, the estimates of cohort-specific effect for the given relative time are extracted from {cmd:e()} 
and reported in {cmd:e(b_interact)}
 as well as the variance associated with each estimator in  {cmd:e(V_interact)}.
In summary, the following results are stored in {cmd:e()}:

{synoptset 24 tabbed}{...}

{syntab:Matrices}
{synopt:{cmd:e(b_iw)}}IW estimate vector{p_end}
{synopt:{cmd:e(V_iw)}}pointwise variance covariance estimate of the IW estimators, which can be used as input of pre-trend test such as {browse "https://github.com/jonathandroth/pretrends":pretrends}{p_end}
{synopt:{cmd:e(b_interact)}}Each column vector contains estimates of cohort-specific effect for the given relative time. {p_end}
{synopt:{cmd:e(V_interact)}}Each column vector contains variance estimate of the cohort-specific effect estimator for the given relative time. {p_end}
{synopt:{cmd:e(ff_w)}}Each column vector contains estimates of cohort shares underlying the given relative time. {p_end}
{synopt:{cmd:e(Sigma_ff)}}variance estimate of the cohort share estimators{p_end}

{synoptline}
{p 4 6 2}
{opt aweight}s and {opt fweight}s are allowed;
see {help weight}.
{p_end}
 
{marker description}{...}
{title:Description}

{pstd}
To estimate the dynamic effects of an absorbing treatment, researchers often use two-way fixed effects regressions that include leads and lags of the treatment (event study specification). Units are categorized into different cohorts based on their initial treatment timing. Sun and Abraham (2020) show the coefficients in this event study specification can be written as a linear combination of cohort-specific effects from both its own relative period and other relative periods.  
They show this specification is not robust to treatment effects heterogeneity and propose the interaction weighted estimator.

{pstd}
{opt eventstudyinteract} implements the interaction weighted estimators for event studies, 
It is optimized for speed in large panel datasets thanks to {helpb reghdfe}.

{pstd}
For each relative time indicator specified in {it:rel_time_list}, {opt eventstudyinteract} estimates the IW estimator for the treatment effect associated with the given relative time. 
It provides built-in options to control for fixed effects and covariates
(see {help eventstudyinteract##syntax:covariates}).    


{marker examples}{...}
{title:Examples}

{pstd}Load the 1968 extract of the National Longitudinal Survey of Young Women and Mature Women.{p_end}
{phang2}. {stata webuse nlswork, clear}{p_end}

{pstd}Code the cohort categorical variable based on when the individual first joined the union, 
which will be inputted in {opth cohort(varname)}.{p_end}
{phang2}. {stata gen union_year = year if union == 1 }{p_end}
{phang2}. {stata "bysort idcode: egen first_union = min(union_year)"}{p_end}
{phang2}. {stata drop union_year }{p_end}
 
{pstd}Code the relative time categorical variable.{p_end}
{phang2}. {stata gen ry = year - first_union}{p_end}

{pstd} For the first example, we take the control cohort to be individuals that never unionized.{p_end}
{phang2}. {stata gen never_union = (first_union == .)}{p_end}

{pstd} Check if there is a sufficient number of treated units for each relative time. 
With very few units it might be better to bin the relative times and assume constant treatment effects within the bin. {p_end}
{phang2}. {stata tab ry}{p_end}

{pstd}We will consider the dynamic effect of union status on income. 
We first generate these relative time indicators, and leave out the distant leads due to few observations.  
Implicitly this assumes that effects outside the lead windows are zero.  {p_end}
	{cmd:forvalues k = 18(-1)2 {c -(}}
	{cmd:   gen g_`k' = ry == -`k'}
	{cmd:{c )-}}
	{cmd:forvalues k = 0/18 {c -(}}
	{cmd:     gen g`k' = ry == `k'}
	{cmd:{c )-}}
	
{pstd} We use the IW estimator to estimate the dynamic effect on log wage associated with each relative time.{p_end}
{pstd} With many leads and lags, we need a large matrix size to hold intermediate estimates.{p_end}
{phang2}. {stata set matsize 800 }{p_end}
{phang2}. {stata eventstudyinteract ln_wage g_* g0-g18, cohort(first_union) control_cohort(never_union) covariates(south) absorb(i.idcode i.year) vce(cluster idcode) }{p_end}

{title:Event study plots}
{pstd} We may feed the estimates into {helpb coefplot} for an event study plot.{p_end}
{phang2}. {stata matrix C = e(b_iw)}{p_end}
{phang2}. {stata mata st_matrix("A",sqrt(diagonal(st_matrix("e(V_iw)"))))}{p_end}
{phang2}. {stata matrix C = C \ A'}{p_end}
{phang2}. {stata matrix list C}{p_end}
{phang2}. {stata coefplot matrix(C[1]), se(C[2])}{p_end}

{title:Binning}
{pstd} Pre-treatment effects seem relatively constant, which might suggest binning the many leads. 
TODO: current implementation of bins does not follow Sun and Abraham (2020) exactly due to coding challenge.  
But it is valid if effects in the bin are constant for each cohort.{p_end}
{phang2}. {stata gen g_l4 = ry <= -4}{p_end}

{title:Using the last treated as the control cohort}
{pstd} Alternatively, we can take the control cohort to be individuals that were unionized last.{p_end}
{phang2}. {stata gen last_union = (first_union == 88)}{p_end}

{pstd} If using the last-treated cohort as the control, be sure to restrict the analysis sample to exclude the never-treated (if any) and to be before 
the treated periods for the last-treated cohort.{p_end}
{phang2}. {stata eventstudyinteract ln_wage g_l4 g_3 g_2 g0-g18 if first_union != . & year < 88, cohort(first_union) control_cohort(last_union) covariates(south) absorb(i.idcode i.year) vce(cluster idcode) }{p_end}

{title:Understanding the mechanics of the IW estimator}
{pstd} We can look at the share of cohorts underlying the IW estimates for each relative time.{p_end}
{phang2}. {stata matrix list e(ff_w) }{p_end}

{pstd} We can look at the cohort-specific treatment effect estimates for each relative time.{p_end}
{phang2}. {stata matrix list e(b_interact) }{p_end}

{pstd} We can check that the IW estimates are weighted averages of the cohort-specific dynamic effect estimate 
, weighted by the corresponding cohort share estimates.  For example, the IW estimate associated with g_l4 is {p_end}
{phang2}. {stata matrix list e(b_iw)}{p_end}
{pstd} which is the weighted average of cohort-specific treatment effect estimates, 
with weights corresponding to the cohort share estimates: {p_end}
{phang2}. {stata matrix delta = e(b_interact)}{p_end}
{phang2}. {stata matrix weight = e(ff_w)}{p_end}
{phang2}. {stata matrix nu = delta[1...,1]'*weight[1...,1]}{p_end}
{phang2}. {stata matrix list nu}{p_end}

{title:Aggregating event study estimates}
{pstd} It is possible to use {helpb lincom} to estimate the average effect, say over the first five years of joining the union. However, since {helpb lincom} looks for coefficients and variance covariance matrix stored in {cmd:e(b)} 
and {cmd:e(V)} a workaround is the following: {p_end}
{phang2}. {stata matrix b = e(b_iw)}{p_end}
{phang2}. {stata matrix V = e(V_iw)}{p_end}
{phang2}. {stata ereturn post b V}{p_end}
{phang2}. {stata lincom (g0 + g1 + g2 + g3 + g4)/5}{p_end}

{title:Aggregating event study estimates}
{pstd} It is possible to use {helpb test} to perform a joint F-test of pretrends in the sense of testing whether all of the coefficients on the pre-event relative time indicators are jointly zero. However, since {helpb test} looks for coefficients and variance covariance matrix stored in {cmd:e(b)} 
and {cmd:e(V)} a workaround is the following: {p_end}
{phang2}. {stata matrix b = e(b_iw)}{p_end}
{phang2}. {stata matrix V = e(V_iw)}{p_end}
{phang2}. {stata ereturn post b V}{p_end}
{phang2}. {stata test (g_l4=0) (g_3=0) (g_2=0)}{p_end}

{title:Compare event study estimates for subsamples}
{pstd} Suppose we want to compare the average effect over the first five years of joining the union between college graduates and non-college graduates. We can first estimate their separate effects by interacting the relative time indicators with the indicator of college graduates: {p_end}
	{cmd:forvalues k = 18(-1)2 {c -(}}
	{cmd:   gen g_`k'_collgrad0 = ry == -`k' & collgrad == 0}
	{cmd:{c )-}}
	{cmd:forvalues k = 0/18 {c -(}}
	{cmd:     gen g`k'_collgrad0 = ry == `k' & collgrad == 0}
	{cmd:{c )-}}
	{cmd:gen g_l4_collgrad0 = ry <= -4 & collgrad == 0} 
	{cmd:forvalues k = 18(-1)2 {c -(}}
	{cmd:   gen g_`k'_collgrad1 = ry == -`k' & collgrad == 1}
	{cmd:{c )-}}
	{cmd:forvalues k = 0/18 {c -(}}
	{cmd:     gen g`k'_collgrad1 = ry == `k' & collgrad == 1}
	{cmd:{c )-}}
	{cmd:gen g_l4_collgrad1 = ry <= -4 & collgrad == 1}

{pstd} We can then use {helpb lincom} to estimate the difference in their average effects as below.  Alternatively, we can use {helpb eventstudyinteract} separately on the subsamples of college graduates and non-college graduates. 
The point estimates might be slightly different because the control cohort is restricted to college graduates and non-college graduates respectively. The approach below combines both into one control cohort. {p_end}	
{phang2}. eventstudyinteract ln_wage g_l4_collgrad* g_3_collgrad* g_2_collgrad* g0_collgrad0-g18_collgrad0  g0_collgrad1-g18_collgrad1 if first_union != . & year < 88, cohort(first_union) control_cohort(last_union)  absorb(i.idcode i.year) 
vce(cluster idcode)  {p_end}
{phang2}. {stata matrix b = e(b_iw)}{p_end}
{phang2}. {stata matrix V = e(V_iw)}{p_end}
{phang2}. {stata ereturn post b V}{p_end}
{phang2}. {stata lincom (g0_collgrad1 + g1_collgrad1 + g2_collgrad1 + g3_collgrad1 + g4_collgrad1)/5 - (g0_collgrad0 + g1_collgrad0 + g2_collgrad0 + g3_collgrad0 + g4_collgrad0)/5}{p_end}

{marker acknowledgements}{...}
{title:Acknowledgements}
  
{pstd}Thanks to the users of early versions of the program who devoted time to reporting
the bugs that they encountered.  Thanks to Yunan Ji, Soomi Kim, Paichen Li, Emma Rackstraw and Jie Zhou for beta testing.  Thanks to Claudio A. Mora-García for incorporating covariance estimation into the code.
 
{marker references}{...}
{title:References}
 
{marker BS2013}{...}
{phang}
Baum, C. and Schaffer, M. 2013. 
AVAR: Stata module to perform asymptotic covariance estimation for iid and non-iid data robust to heteroskedasticity, autocorrelation, 1- and 2-way clustering, and common cross-panel autocorrelated disturbances.
Statistical Software Components S457689, Boston College Department of Economics.
{browse "https://ideas.repec.org/c/boc/bocode/s457689.html":https://ideas.repec.org/c/boc/bocode/s457689.html}
{p_end}
 
{marker SC2017}{...}
{phang}
Correia, S. 2017. 
REGHDFE: Stata module for linear and instrumental-variable/gmm regression absorbing multiple levels of fixed effects. 
Statistical Software Components s457874, Boston College Department of Economics. 
{browse "https://ideas.repec.org/c/boc/bocode/s457874.html":https://ideas.repec.org/c/boc/bocode/s457874.html}
{p_end}

{marker SA2020}{...}
{phang}
Sun, L. and Abraham, S. 2020.
Estimating Dynamic Treatment Effects in Event Studies with
Heterogeneous Treatment Effects
{p_end}

{marker citation}{...}
{title:Citation and Installation of eventstudyinteract}

{pstd}{opt eventstudyinteract} is not an official Stata command. It is a free contribution
to the research community, like a paper. Please cite it as such: {p_end}

{phang}Sun, L., 2021.
eventstudyinteract: interaction weighted estimator for event study.
{browse "https://github.com/lsun20/eventstudyinteract":https://github.com/lsun20/eventstudyinteract}.

{pstd}{opt eventstudyinteract} can be installed easily via the {helpb github} package, which is available on 
{browse "https://github.com/haghish/github":https://github.com/haghish/github}. {p_end}

{phang2}. {stata github install lsun20/eventstudyinteract }{p_end}
{phang2}. {stata github update eventstudyinteract }{p_end}

{marker author}{...}
{title:Author}

{pstd}Liyang Sun{p_end}
{pstd}lsun20@mit.edu{p_end}
