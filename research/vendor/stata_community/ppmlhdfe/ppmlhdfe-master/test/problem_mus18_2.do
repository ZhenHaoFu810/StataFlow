noi cscript "ppmlhdfe: test against corner case in tiny sample of mus18 dataset" adofile ppmlhdfe
set linesize 150


clear
input byte(id y year) double age
1  7 2 63.02327346801758
1 14 3 64.02326965332031
2  5 1 30.91581153869629
2  2 2 31.91581153869629
3  0 1  30.8117733001709
3  2 2  31.8117733001709
end


* [TEST]

	* Run ppmlhdfe
	ppmlhdfe y year age, a(id)

exit
