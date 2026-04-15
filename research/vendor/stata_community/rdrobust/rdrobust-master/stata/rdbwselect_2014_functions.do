*!version 6.0  2014-10-14

capture mata mata drop rdbwselect_2014_rdvce()
mata
real matrix rdbwselect_2014_rdvce(real matrix X, real matrix y, real matrix z, real scalar p, real scalar h, real scalar matches, string vce, string kernel)
{
n = length(X)
p1 = p+1
sigma = J(n,1, .)
if (vce=="resid") {
	for (k=1; k<=n; k++) {
		cutoff = X[k]
		W = rdbwselect_2014_kweight(X,cutoff,h,kernel)
		W_p = select(W, W:> 0)
		X_p = select(X, W:> 0)
		y_p = select(y, W:> 0)
		z_p = select(z, W:> 0)
		XX  = J(length(W_p),p1,.)
		for (j=1; j<=p1; j++) {
			XX[.,j] = (X_p:-cutoff):^(j-1)
		}
	m_p_y = invsym(cross(XX,W_p,XX))*cross(XX,W_p,y_p)
	m_p_z = invsym(cross(XX,W_p,XX))*cross(XX,W_p,z_p)
	sigma[k] = (y[k] - m_p_y[1])*(z[k] - m_p_z[1])
	}
}
else  {
v = w = 0
for (k=1; k<=n; k++) {
	x_abs = abs(X :- X[k,1])
	diffx = select(x_abs, x_abs:> 0)
	diffy = select(y, x_abs:> 0)
	diffz = select(z, x_abs:> 0)
	minindex(diffx, matches, v, w)
	Ji=length(v)
	y_match_avg = mean(diffy[v])
	z_match_avg = mean(diffz[v])
	sigma[k] = (Ji/(Ji+1))*(y[k] :- y_match_avg):*(z[k] :- z_match_avg)
	}
}
return(sigma)
}
mata mosave rdbwselect_2014_rdvce(), replace
end

capture mata mata drop rdbwselect_2014_kweight()
mata
real matrix rdbwselect_2014_kweight(real matrix X, real scalar c, real scalar h, string kernel)
{
u = (X:-c)/h
	if (kernel=="epanechnikov" | kernel=="epa") {
	w = (0.75:*(1:-u:^2):*(abs(u):<=1))/h
	}
	else if (kernel=="uniform" | kernel=="uni") {
	w = (0.5:*(abs(u):<=1))/h
	}
	else {
	w = ((1:-abs(u)):*(abs(u):<=1))/h
	}	
return(w)	
}
mata mosave rdbwselect_2014_kweight(), replace
end

capture mata mata drop rdbwselect_2014_regconst()
mata
real matrix rdbwselect_2014_regconst(real scalar d, real scalar h)
{
d2 = 2*d+1
d1 = d+1
mu = J(d2, 1, 0)
mu[1] = 1
XX = J(d1,d1,0)
for (j=2; j<=d2; j++) {
i = j-1
	if (mod(j,2)==1) {
		mu[j] = (1/(i+1))*(h/2)^i
	}
}
for (j=1; j<=d1; j++) {
	XX[j,.] = mu[j::j+d]'
}
invXX =invsym(XX)
return(invXX)
}
mata mosave rdbwselect_2014_regconst(), replace
end

capture mata mata drop rdbwselect_2014_cvplot()
mata
void rdbwselect_2014_cvplot(
 real colvector y,
 real colvector x,
 | string scalar opts)
{
	real scalar n, N, Y, X

	n = rows(y)
	if (rows(x)!=n) _error(3200)
	N = st_nobs()
	if (N<n) st_addobs(n-N)
	st_store((1,n), Y=st_addvar("double", st_tempname()), y)
	st_store((1,n), X=st_addvar("double", st_tempname()), x)
	stata("twoway scatter " + st_varname(Y) + " " +
	 st_varname(X) + ", " + opts)
	if (N<n) st_dropobsin((N+1,n))
	st_dropvar((Y,X))
}
mata mosave rdbwselect_2014_cvplot(), replace
end






