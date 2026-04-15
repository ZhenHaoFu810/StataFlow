*ppmlhdfe, reload
*pr drop _all
*cls

// X1 >= 0; but we can't use X2
ppmlhdfe, simplex( (1, 1, 0, 0 \ 12, 0, -5, 6)' ) ans(0, 0, 1, 1)

// 13 * X1 - X2 = (1, 13, 5, 0) >= 0
ppmlhdfe, simplex( (1, 1, 0, 0 \ 12, 0, -5, 0)' ) ans(0, 0, 0, 1)

// no separation
ppmlhdfe, simplex( (-1, 1, 0, 0 \ 12, 0, -5, 0)' ) ans(1, 1, 1, 1)

// 1st obs separated by X1
ppmlhdfe, simplex( (1, 0, 0)' ) ans(0, 1, 1)

// 1st and only obs separated by X1
ppmlhdfe, simplex( (1)' ) ans(0)

// X1 is just zeroes
ppmlhdfe, simplex( (0, 0, 0)' ) ans(1, 1, 1)

// X1 + X2 + X3 = (-1, -1, -1, 0), so obs 1 to 3 are separated
ppmlhdfe, simplex( (1, -1, -1, 0 \ -1, 1, -1, 0 \ -1, -1, 1, 0)' ) ans(0, 0, 0, 1)

// X2 + X3 separate obs #1
ppmlhdfe, simplex( (1, -1, -1, 1 \ -1, 1, -1, 0 \ -1, -1, 1, 0)' ) ans(0, 1, 1, 1)

// Several variables that are the same
ppmlhdfe, simplex( (1, 2, -3, -4 \ 1, 2, -3, -4 \ 1, 2, -3, -4 \ 1, 2, -3, -4)' ) ans(1, 1, 1, 1)
ppmlhdfe, simplex( (1, 2, -3, -4 \ 1, 2, -3, -4 \ 1, 2, -3, -4 \ 1, 2, -3, -4 \ 1, 2, -3, -4)' ) ans(1, 1, 1, 1)


// Variables are collinear: X1 = X2 = X3
ppmlhdfe, simplex( (1, 2, -3, -4 \ 2, 4, -6, -8 \ 3, 6, -9, -12)' ) ans(1, 1, 1, 1)
// Variables are collinear: X1 + X2 = X3
ppmlhdfe, simplex( (1, 2, -3, -4 \ 2, -2, 0, 0 \ 3, 0, -3, -4)' ) ans(1, 1, 1, 1)
// X2 = 10 X1
ppmlhdfe, simplex( (.3 , -2 \ 3 , -20)' ) ans(1, 1)


// Corner case, N=K: both X1 and X2 separate obs 1-2
ppmlhdfe, simplex( (.3, 1 \ -2, -1)' ) ans(0, 0)

// As above but with a vector of zeroes
ppmlhdfe, simplex( (.3, 1, 0 \ -2, -1, 0)' ) ans(0, 0, 1)


exit
