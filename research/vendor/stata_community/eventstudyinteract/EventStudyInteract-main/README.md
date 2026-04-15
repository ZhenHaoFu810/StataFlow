# EventStudyInteract

**eventstudyinteract** is a Stata package that implements the interaction weighted estimator for an event study.  Sun and Abraham (2020) proposes this estimator as an alternative to the canonical two-way fixed effects regressions with relative time indicators.  Sun and Abraham (2020) proves that this estimator is consistent for the average dynamic effect at a given relative time even under heterogeneous treatment effects.  As outlined in the paper, **eventstudyinteract** uses either never-treated units or last-treated units as the comparison group. A similar estimator is Callaway and Sant'Anna (2020), which uses all not-yet-treated units for comparison.  

**eventstudyinteract** also constructs pointwise confidence intervals valid for the effect at a given relative time.  The bootstrap-based inference by Callaway and Sant'Anna (2020) constructs simultaneous confidence intervals that are valid for the entire path of dynamic effects, i.e., effects across multiple relative times.  

[Callaway and Sant'Anna (2020)](https://bcallaway11.github.io/did/) provides an R package `did`  for their estimation and inference procedure.

## Installation
**eventstudyinteract** can be installed easily via the `github` package, which is available at [https://github.com/haghish/github](https://github.com/haghish/github).  Specifically execute the following code in Stata:

`net install github, from("https://haghish.github.io/github/")`

To install the **eventstudyinteract** package , execute the following in Stata:

`github install lsun20/eventstudyinteract`

which should install the dependency packages.  If not working, try manually install

`ssc install avar`  
`ssc install reghdfe`  
`ssc install ftools`  

If you run into an error message of `class FixedEffects undefined`, this can usually be resolved by `reghdfe, compile` as suggested by the repository of [reghdfe](https://github.com/sergiocorreia/reghdfe/issues/181).

To update the **eventstudyinteract**  package, execute the following in Stata:

`github update eventstudyinteract`

Documentation is included in the Stata help file that is installed along with the package.  An empirical example is provided in the help file.

## Authors and acknowledgment
Liyang Sun

Preprint of Sun and Abraham (2020) is available on [my personal website](https://lsun20.github.io/event_studies_paper.pdf).