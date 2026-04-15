noi cscript "ppmlhdfe: test against corner case in tiny sample of mus18 dataset" adofile ppmlhdfe
set linesize 150


clear
input byte year float(id age) byte y
3 126384  64.02327 14
1 126388 31.485285  1
1 126556  31.86311  2
1 126859  30.91581  5
1 129500 30.811773  0
2 129500 31.811773  2
end


* [TEST]

	* Run ppmlhdfe
	ppmlhdfe y year age, keepsing a(id)

exit
