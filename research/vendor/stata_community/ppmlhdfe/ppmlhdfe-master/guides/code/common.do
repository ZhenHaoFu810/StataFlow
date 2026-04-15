* ===========================================================================
* Common Settings & Global Variables
* ===========================================================================
	version 18
	clear all
	set type double // -gen xyz- will default to -double- instead of -float-
	set varabbrev off // too many hidden errors otherwise
	set emptycells drop
	set trace off
	cap cls
	set rmsg off


// --------------------------------------------------------------------------
// Dependencies
// --------------------------------------------------------------------------
	cap which require
	if (c(rc)) net install require, from(ssc)
	require setroot >= 1.0, install
	require mdesc, install
	require ftools >= 2.49.1	, install from("https://raw.githubusercontent.com/sergiocorreia/ftools/master/src/")
	require reghdfe >= 6.12.5	, install from("https://raw.githubusercontent.com/sergiocorreia/reghdfe/master/src/")
	require ppmlhdfe >= 2.3.1 	, install from("https://raw.githubusercontent.com/sergiocorreia/ppmlhdfe/master/src/")
