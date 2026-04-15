{smcl}
{* *! version 1.1.4 29nov2025}{...}
{vieweralsosee "ivreg" "help ivreg2"}{...}
{vieweralsosee "reghdfe" "help reghdfe"}{...}
{vieweralsosee "ftools" "help ftools"}{...}
{vieweralsosee "[R] ivregress" "help ivregress"}{...}
{vieweralsosee "" "--"}{...}
{title:Title}

{p2colset 5 18 20 2}{...}
{p2col :{cmd:ivreghdfe} {hline 2}}Extended instrumental variable regressions with multiple levels of fixed effects{p_end}
{p2colreset}{...}

{marker syntax}{...}
{title:Syntax}

{pstd}
{cmd:ivreghdfe} is essentially {help ivreg2} with an additional {help reghdfe##options:absorb()} option from {cmd:reghdfe}. See the links above for the detailed help files of each program.

{pstd}
To use {cmd:ivreghdfe}, you must have installed three packages: {cmd: ftools}, {cmd: reghdfe}, and {cmd: ivreg2}
(see the {browse "https://github.com/sergiocorreia/ivreghdfe#installation":online guide}). 

{pstd}
You can also pass additional reghdfe optimization options directly:

{phang2}{stata sysuse auto}{p_end}
{phang2}{stata ivreghdfe price weight (length=gear), absorb(rep78) tol(1e-6)}{p_end}
{phang2}{stata ivreghdfe price weight (length=gear), absorb(rep78) accel(none)}{p_end}


{title:Citation}

Please cite the ivreg2 and/or reghdfe commands directly:

{phang}Baum, C.F., Schaffer, M.E., Stillman, S. 2010.
ivreg2: Stata module for extended instrumental variables/2SLS, GMM and AC/HAC, LIML and k-class regression.
{browse "http://ideas.repec.org/c/boc/bocode/s425401.html":http://ideas.repec.org/c/boc/bocode/s425401.html}{p_end}

{phang}Correia, Sergio. 2017.
Linear Models with High-Dimensional Fixed Effects: An Efficient and Feasible Estimator (Working Paper)
{browse "https://github.com/sergiocorreia/reghdfe/#citation":https://github.com/sergiocorreia/reghdfe/#citation}{p_end}


{title:Support for margins}

Note that there is experimental support for the {cmd:margins} postestimation command, but it hasn't been tested with advanced options such as nonlinear expressions.


{title:Feedback}

For any issues or suggestions, please see the {browse "https://github.com/sergiocorreia/ivreghdfe":Github} website, including the {browse "https://github.com/sergiocorreia/ivreghdfe/issues":issue tracker}.


{title:ivreg2 Authors}

        Christopher F Baum, Boston College, USA
        baum@bc.edu

        Mark E Schaffer, Heriot-Watt University, UK
        m.e.schaffer@hw.ac.uk

        Steven Stillman, Motu Economic and Public Policy Research
        stillman@motu.org.nz


{title:reghdfe Author}

{pstd}Sergio Correia{break}
Board of Governors of the Federal Reserve{break}
Email: {browse "mailto:sergio.correia@gmail.com":sergio.correia@gmail.com}
{p_end}
