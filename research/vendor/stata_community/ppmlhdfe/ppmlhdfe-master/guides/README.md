# Practical companion to "Verifying the existence of maximum likelihood estimates for generalized linear models" (Correia, Guimarães, Zylkin)

This companion consists of three documents, plus a suit of test datasets, that complement the paper:

> Sergio Correia, Paulo Guimarães, Thomas Zylkin: "Verifying the existence of maximum likelihood estimates for generalized linear models"

The documents are:

1. [*Primer on nonexistence of estimates and statistical separation for Poisson models*](https://github.com/sergiocorreia/ppmlhdfe/blob/master/guides/nonexistence_primer.md): introductory guide to understanding the non-existence problem, with a focus on on Poisson models. Also discusses how to detect this issue, and explains solutions including our "iterative rectifier" method.
2. [*Examples of nonexistence of estimates for Poisson, Logit, and Multinomial Logit models*](https://github.com/sergiocorreia/ppmlhdfe/blob/master/guides/nonexistence_examples.md): discusses several canonical examples of non-existence and how our "iterative rectifier" addresses them. Examples include Logit, Multinomial Logit, and Poisson. Further presents seventeen new Poisson examples that can be used to test software implementation of existing separation algorithms as well as to benchmark the performance of future algorithms.
3. [*Nonexistence of estimates of Poisson models across different statistical packages*](https://github.com/sergiocorreia/ppmlhdfe/blob/master/guides/nonexistence_benchmarks.md): documents how non-existence affects some of the most popular statistical packages (Stata, R, Julia, Matlab), with either non-convergence or convergence to incorrect solutions.

Also see:

- [*Main page for the `ppmlhdfe` Stata package](https://github.com/sergiocorreia/ppmlhdfe), including some [undocumented options](https://github.com/sergiocorreia/ppmlhdfe/blob/master/guides/undocumented.md) that can be used to illustrate and diagnose non-existence issues.
- [*Suite of 17 poisson examples exhibiting non-existence*](https://github.com/sergiocorreia/ppmlhdfe/tree/master/guides/separation_datasets)

