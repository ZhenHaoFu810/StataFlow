insheet using C:\Users\Sergio\Documents\glm2_crabs.csv, clear tab

su width
gen double width_shifted = width - r(min)
gen byte Dark = dark == "yes"
gen byte Goodspine = goodspine == "yes"

mata: data = st_data(., "satellites width_shifted Dark Goodspine")
mata: index = st_data(., "rep1")
mata: data = data[index, .]
set obs 173
mata: st_store(., tokens("satellites width_shifted Dark Goodspine"), data)

glm satellites width_shifted i.Dark i.Goodspine, fam(poi) // irls
ppmlhdfe satellites width_shifted, a(Dark Goodspine) keepsing
