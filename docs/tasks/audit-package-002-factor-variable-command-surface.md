# 瀹¤鍚庝换鍔″寘 002锛歋tata 鍥犲瓙鍙橀噺銆佷氦涔橀」涓?`absorb()` 鍛戒护灞傝涔?
## 1. 浠诲姟鑳屾櫙

褰撳墠椤圭洰宸茬粡鏈夎緝瀹屾暣鐨勪及璁″櫒鍐呮牳涓?`compat.stata` wrapper锛屼絾 **Stata 鍥犲瓙鍙橀噺璇箟鍩烘湰缂哄け**锛宍absorb()` 鐨勫懡浠ゅ眰璇硶涔熻繕涓嶅畬鏁淬€?
杩欐剰鍛崇潃涓嬮潰杩欑被楂橀鍐欐硶鐩墠骞朵笉鑳戒綔涓虹湡姝ｇ殑 Stata 鍛戒护杩佺Щ浣撻獙鏉ヤ娇鐢細

- `reghdfe y c.x1#c.x2`
- `reghdfe y c.x1##c.x2`
- `reghdfe y i.industry##c.post`
- `reghdfe y i.treat##i.post`
- `regress y c.x1##c.x2`
- `poisson y c.x1##c.x2`
- `reghdfe y x1##x2, absorb(firm year)`

杩欐槸涓€涓湡瀹炵殑鍛戒护灞傜己鍙ｏ紝鑰屼笉鏄€滆娉曠硸闂鈥濄€傚瀹炶瘉鐮旂┒鑰呮潵璇达紝`#` 鍜?`##` 鐨勮涔夊氨鏄懡浠ゆ湰韬殑涓€閮ㄥ垎锛?
- `c.x1#c.x2` 鍙寘鍚氦涔橀」
- `c.x1##c.x2` 鍖呭惈 `x1`銆乣x2` 鍜?`x1*x2`
- `i.a#i.b` 琛ㄧず鍒嗙被鍙橀噺浜や簰铏氭嫙鍙橀噺
- `i.a##c.x` 琛ㄧず鍒嗙被涓绘晥搴斻€佽繛缁富鏁堝簲鍜屼氦浜掗」鐨勫畬鏁村睍寮€

鍚屾椂锛宍reghdfe y x1##x2, absorb(firm year)` 杩欑被鍛戒护杩樻湁涓€涓叧閿涔夛細

- 涓绘晥搴斿彲鑳藉洜涓?absorbed FE 鑰岃瀹屽叏鍏辩嚎骞惰鐪佺暐
- 浣嗕氦浜掗」濡傛灉浠嶆湁缁勫唴鍙樺寲锛屽簲璇ョ户缁彲璇嗗埆

杩欎笉鏄壒娈婅竟瑙掓儏鍐碉紝鑰屾槸 `reghdfe`/`areg`/闈㈡澘瀹炶瘉涓殑甯歌鐢ㄦ硶銆?
濡傛灉娌℃湁杩欏眰鏀寔锛屽綋鍓嶅簱铏界劧鏁板€煎唴鏍稿己锛屼絾浠嶄笉鏄敤鎴峰彲鐩存帴杩佺Щ鐨?Stata 椋庢牸搴撱€?
## 2. 鎬荤洰鏍?
鏈疆瑕佸缓绔?**Stata 鍥犲瓙鍙橀噺璇箟鐨勭涓€闃舵鍛戒护灞傚疄鐜?*锛屽苟鎶婂畠鎺ュ叆褰撳墠楂橀 wrapper 鍛戒护锛屽悓鏃惰ˉ涓?`absorb()` 鐨勫父瑙佸懡浠ゅ眰璇硶銆?
閲嶇偣涓嶆槸鈥滃噾鍑轰笌鎵嬪伐鏋勯€犱氦涔樺垪鐩稿悓鐨勭粨鏋溾€濓紝鑰屾槸锛?
1. 鏄庣‘寤烘ā璇箟鏄惁涓?Stata 瀵瑰簲
2. 鏄庣‘璁捐鐭╅樀鏋勯€犺繃绋嬫槸鍚︿笌 Stata 鍥犲瓙鍙橀噺瑙勫垯涓€鑷?3. 鏄庣‘ wrapper 鏄惁鐪熸鎺ュ彈 Stata 椋庢牸椤瑰苟姝ｇ‘灞曞紑
4. 鏄庣‘ absorbed FE 涓庡洜瀛愬彉閲忎富鏁堝簲/浜や簰椤圭殑鍏辩嚎鎬у鐞嗘槸鍚︿笌 Stata 琛屼负涓€鑷?
## 3. 鏈疆蹇呴』瀹屾垚鐨勮寖鍥?
### A. 寤虹珛鍥犲瓙鍙橀噺瑙ｆ瀽涓庡睍寮€灞?
鏂板涓€涓笓闂ㄧ殑鍛戒护灞傝涔夋ā鍧楋紝寤鸿鏀惧湪锛?
- `src/stataflow/compat/stata/factor_variables.py`

鑷冲皯鏀寔浠ヤ笅璇硶锛?
- `x1`
- `c.x1`
- `i.g1`
- `c.x1#c.x2`
- `c.x1##c.x2`
- `i.g1#i.g2`
- `i.g1##i.g2`
- `i.g1#c.x1`
- `i.g1##c.x1`

鏈疆鍏佽鍙敮鎸?**杩炵画鍙橀噺涓庡垎绫诲彉閲?* 鐨勪竴闃?`# / ##` 灞曞紑锛屼笉寮鸿涓€娆″仛瀹屾暣 Stata factor grammar锛屼絾涓嶈兘鍙仛杩炵画鍙橀噺瀛愰泦銆?
闇€瑕佹槑纭竴涓粯璁よ鍒欙細

- 鏅€氳８鍙橀噺 `x1` 鍦?estimator 灞備粛浣滀负鏅€氬垪澶勭悊
- Stata factor 璇箟鍙湪鏄惧紡 `c.` / `i.` 鏍囪鎴?`#` / `##` term 涓Е鍙?- 涓嶅厑璁稿瑁稿彉閲忓伔鍋风寽娴嬩负 `i.` 鎴?`c.`

### B. 鏄庣‘鏈疆鏀寔涓庢嫆缁濊竟鐣?
蹇呴』鏄惧紡澶勭悊锛岃€屼笉鏄潤榛樻帴鍙楋細

- 瀵规湰杞敮鎸佺殑璇硶锛氭甯稿睍寮€
- 瀵规湰杞殏涓嶆敮鎸佺殑璇硶锛氱洿鎺?`ValueError`

鑷冲皯瑕佹樉寮忔嫆缁濓細

- `ib#.var`
- `o.var`
- `b.var`
- 鏃堕棿搴忓垪绠楀瓙濡?`L.x`
- 涓夐樁鍙婁互涓婂洜瀛愪氦浜?- 鏇撮珮闃跺鏉傜粍鍚?- 鏈疆鏈疄鐜扮殑浠绘剰 factor 璇硶鍙樹綋

涓嶈兘鍑虹幇鈥滃瓧绗︿覆琚杩涙潵浣嗗綋鏅€氬彉閲忓悕蹇界暐澶勭悊鈥濈殑鎯呭喌銆?
### C. 鎺ュ叆楂橀 wrapper 鍛戒护

鑷冲皯鎺ュ叆浠ヤ笅 wrapper锛?
- `regress`
- `areg`
- `reghdfe`
- `ivregress_2sls`
- `ivreghdfe`
- `logit`
- `probit`
- `poisson`
- `ppmlhdfe`

瑕佹眰鏄細

- `x` 鍙傛暟涓厑璁告贩鍚堟櫘閫氬彉閲忓悕鍜?factor-term
- wrapper 鍐呴儴璐熻矗鎶?term 灞曞紑鎴愯璁＄煩闃靛垪
- 缁撴灉瀵硅薄涓繚鐣欑ǔ瀹氥€佸彲棰勬祴銆佸敖閲忔帴杩?Stata 涔犳儻鐨勫垪鍚?- `absorb` 鍙傛暟蹇呴』鏀寔锛?  - `absorb="firm"`
  - `absorb=["firm", "year"]`
  - `absorb="firm year"` 杩欑 Stata 椋庢牸绌烘牸鍒嗛殧鍐欐硶

### D. absorbed FE 涓庡洜瀛愰」鍏辩嚎鎬ц涔?
鏈疆蹇呴』鏄惧紡瑕嗙洊浠ヤ笅鍦烘櫙锛?
- `reghdfe y c.x1##c.x2, absorb(firm year)`
- `reghdfe y i.treat##c.post, absorb(firm year)`
- `reghdfe y i.treat##i.post, absorb(firm year)`

瑕佹眰涓嶆槸鈥滃己杩富鏁堝簲閮戒繚鐣欌€濓紝鑰屾槸锛?
- 鑻ヤ富鏁堝簲琚?FE 瀹屽叏鍚告敹锛屽簲鎸?Stata 椋庢牸璇嗗埆涓?omitted / dropped
- 鑻ヤ氦浜掗」浠嶆湁 variation锛屽簲淇濈暀骞朵及璁?- 缁撴灉瀵硅薄銆佽鍛婁俊鎭€佸弬鏁板悕蹇呴』涓庤繖涓€琛屼负涓€鑷?
### E. 鍐欐竻妤氣€滄湰杞笉鏄畬鏁?factor grammar鈥?
鏂板涓€浠界爺绌?浜у搧鏂囨。锛屽缓璁細

- `docs/research/factor-variable-semantics.md`

蹇呴』鍐欐竻锛?
- Stata `#` 涓?`##` 鐨勫綋鍓嶆敮鎸佸瓙闆?- `c.` / `i.` 鐨勫綋鍓嶆敮鎸佸瓙闆?- 褰撳墠 Python 绔浣曟槧灏?- `absorb="firm year"` 濡備綍瑙ｆ瀽
- absorbed FE 涓庝富鏁堝簲/浜や簰椤瑰叡绾挎€ф椂鐨勫綋鍓嶅鐞嗗師鍒?- 鏈疆鏄庣‘涓嶆敮鎸佺殑 factor 璇硶
- 涓嬩竴杞嫢瑕佺户缁墿灞曪紝搴斾紭鍏堝仛浠€涔?
### F. 鏇存柊瀵瑰鏂囨。

鑷冲皯鍚屾鏇存柊锛?
- `README.md`
- `docs/command-support-matrix/regress.md`
- `docs/command-support-matrix/reghdfe.md`
- `docs/command-support-matrix/ivregress_2sls.md`
- `docs/command-support-matrix/ivreghdfe.md`
- `docs/command-support-matrix/logit.md`
- `docs/command-support-matrix/probit.md`
- `docs/command-support-matrix/poisson.md`
- `docs/command-support-matrix/ppmlhdfe.md`

鏂囨。蹇呴』璇氬疄鍖哄垎锛?
- 宸叉敮鎸侊細杩炵画鍙橀噺涓庡垎绫诲彉閲忕殑涓€闃?`#` / `##`
- 宸叉敮鎸侊細`absorb` 鐨?list 鍜岀┖鏍煎垎闅斿瓧绗︿覆
- 鏈敮鎸侊細鏇村鏉?factor grammar 涓庢洿楂橀樁缁勫悎

## 4. 娴嬭瘯瑕佹眰

### A. parser / expansion 鍗曞厓娴嬭瘯

鏂板涓撻棬娴嬭瘯锛岄獙璇侊細

- `["x1"]` 涓?`["c.x1"]` 璇箟涓€鑷?- `["i.g1"]` 浼氱敓鎴愮ǔ瀹氱殑铏氭嫙鍙橀噺灞曞紑骞舵湁鏄庣‘鍩哄噯缁勫鐞?- `["c.x1#c.x2"]` 鍙敓鎴愪氦涔橀」
- `["c.x1##c.x2"]` 鐢熸垚涓婚」 + 浜や箻椤?- `["i.g1#i.g2"]` 鍙敓鎴愪氦浜掗」
- `["i.g1##c.x1"]` 鐢熸垚鍒嗙被涓绘晥搴斻€佽繛缁富鏁堝簲銆佷氦浜掗」
- 娣峰悎 varlist 椤哄簭绋冲畾
- `absorb="firm year"` 浼氳瑙ｆ瀽鎴愪袱涓?absorb 鍙橀噺
- 涓嶆敮鎸佽娉曚細鏄庣‘鎶ラ敊

### B. 涓庢墜宸ユ瀯閫犺璁＄煩闃电殑绛変环娴嬭瘯

鑷冲皯瀵逛互涓嬪懡浠ゅ仛鈥滃懡浠よ涔?vs 鎵嬪伐灞曞紑鈥濈殑绛変环娴嬭瘯锛?
- `regress`
- `reghdfe`
- `poisson` 鎴?`logit`

渚嬪锛?
- `regress(..., x=["c.x1#c.x2"])`
  涓?- `regress(..., x=["x1_x2_manual"])`

缁撴灉搴斾弗鏍间竴鑷淬€?
杩樿鑷冲皯瑕嗙洊涓€涓垎绫诲彉閲忓満鏅紝渚嬪锛?
- `regress(..., x=["i.g1##c.x1"])`
  涓?- 鎵嬪伐 dummy + interaction 灞曞紑鍚庣殑璁捐鐭╅樀

缁撴灉搴斾弗鏍间竴鑷淬€?
### C. Stata 鍙岃窇娴嬭瘯

鑷冲皯鏂板浠ヤ笅 dual-run case锛?
- `regress y c.x1#c.x2`
- `regress y c.x1##c.x2`
- `regress y i.g1##c.x1`
- `reghdfe y c.x1##c.x2, absorb(...)`
- `reghdfe y i.g1##c.x1, absorb(firm year)`
- 涓€涓潪绾挎€у懡浠ょ殑 `##` case锛歚logit`銆乣probit`銆乣poisson` 涓夎€呬换閫夊叾涓€

閲嶇偣姣旇緝锛?
- 绯绘暟
- 鏍囧噯璇?- 妫€楠岀粺璁￠噺
- 缁撴灉鍒楀悕/鍙傛暟璇箟
- 琚惛鏀舵垨鍏辩嚎鍚庤鐪佺暐鐨勪富鏁堝簲琛屼负

### D. 鍙嶁€滃噾鏁板€尖€濊姹?
涓嶈兘鍙仛鈥渇actor syntax -> 鎵嬪伐鏋勯€犲垪 -> 缁撴灉涓€鏍封€濈殑鏈€灏忔祴璇曠劧鍚庡绉板畬鎴愩€?
蹇呴』棰濆璇佹槑锛?
- wrapper 纭疄鐞嗚В浜?Stata term 璇箟
- 涓嶆敮鎸佺殑 term 涓嶄細鎮勬倓婕忔帀鎴栧綋鏅€氬垪鍚嶄娇鐢?- Stata 鍙岃窇鏍蜂緥涓嶆槸闈犲瀹瑰樊鏀捐繃
- absorbed FE 涓庝富鏁堝簲/浜や簰椤圭殑璇嗗埆缁撴灉涓嶆槸闈犵壒鍒ゅ啓姝荤殑

## 5. 绂佹浜嬮」

鏈疆涓嶈鍋氾細

- 瀹屾暣 base-level 璇箟
- 瀹屾暣鏃堕棿搴忓垪绠楀瓙
- 鎵€鏈?`fvvarlist` 鍙樹綋
- 鎵€鏈?Stata factor 璇硶涓€娆″仛瀹?- 鍊熸満鎵╁叾浠栨棤鍏崇畻娉曢潰

鏈疆鐨勭洰鏍囨槸鎶?**杩炵画鍙橀噺 + 鍒嗙被鍙橀噺鐨勪竴闃跺洜瀛愪氦浜掕涔?* 浠ュ強甯歌 `absorb()` 鍐欐硶浣滀负鍛戒护灞傚熀纭€鎵撶墷銆?
## 6. 楠岃瘉瑕佹眰

瀹屾垚鍚庤嚦灏戝洖鎶ワ細

```powershell
python -m pytest tests/test_factor_variables.py -v
python -m pytest tests/test_compat_stata_linear.py tests/test_compat_stata_hdfe.py tests/test_compat_stata_iv.py tests/test_compat_stata_glm.py -v
python -m pytest tests -v
```

濡傛灉鏂板 golden dual-run 娴嬭瘯锛屼篃瑕佸湪鎶ュ憡閲屽崟鍒楄鏄庨€氳繃鎯呭喌銆?
## 7. 瀹屾垚鏍囧噯

鏈疆閫氳繃鐨勬渶浣庢爣鍑嗭細

- 杩炵画鍙橀噺涓庡垎绫诲彉閲忕殑涓€闃?`#` / `##` 璇箟宸茶繘鍏?wrapper 灞?- 楂橀鍛戒护 wrapper 宸插彲鐩存帴鎺ュ彈杩欎簺 term
- `absorb="firm year"` 杩欑被鍛戒护灞傚啓娉曞凡姝ｇ‘瑙ｆ瀽
- 涓嶆敮鎸佽娉曚細鏄庣‘鎷掔粷锛屼笉浼氶潤榛樺拷鐣?- 鑷冲皯 1 涓嚎鎬у懡浠ゃ€? 涓?HDFE 鍛戒护銆? 涓潪绾挎€у懡浠ゅ畬鎴?dual-run 璇佹嵁
- 鑷冲皯 1 涓?absorbed FE 涓嬩富鏁堝簲琚惛鏀朵絾浜や簰椤逛粛鍙瘑鍒殑 case 琚獙璇?- 鏂囨。銆乻upport matrix銆佹姤鍛婂悓姝ヤ竴鑷?
鏈疆鍗充娇閫氳繃锛屼篃**涓嶄唬琛ㄥ畬鏁?Stata factor-variable grammar 宸插疄鐜?*銆傚鏋?Claude Code 鍦ㄦ姤鍛婇噷鎶婃湰杞じ澶ф垚鈥淪tata 鍥犲瓙鍙橀噺宸插畬鏁存敮鎸佲€濓紝瑙嗕负鏈畬鎴愩€?