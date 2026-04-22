# 瀹¤鍚庝换鍔″寘 005锛欶actor Variable Phase D 涓庢洿瀹屾暣 `fvvarlist` 瀛愰泦

## 1. 浠诲姟鑳屾櫙

浠诲姟鍖?002 鍒?004 宸茬粡鎶婁互涓嬮珮棰?factor 璇箟鎺ュ叆 wrapper 灞傦細

- `c.x1#c.x2`
- `c.x1##c.x2`
- `i.g1#i.g2`
- `i.g1##i.g2`
- `i.g1#c.x1`
- `i.g1##c.x1`
- `c.x1##i.g1`
- `x1##x2`
- `x1##i.g`
- `ib#.` / `b#.` / `o#.` 鐨勬渶灏?base-level / omitted-level 璇箟

杩欎竴灞傚凡缁忚鐩栦簡澶ч噺甯歌鍥炲綊鍐欐硶锛屼絾浠嶇劧涓?Stata 鐪熷疄 `fvvarlist` 浣跨敤浣撻獙鏈夋槑鏄惧樊璺濓紝灏ゅ叾鏄細

- 涓夐樁 `##` 鐨勫父瑙佸叏鍥犲瓙灞曞紑
- `c.(x1 x2)`銆乣i.(g1 g2)` 杩欑被鎷彿缂╁啓
- 涓婅堪璇箟鍦?`reghdfe`銆乣ivreghdfe`銆侀潪绾挎€у懡浠や腑鐨勪竴鑷磋瘉鎹?
濡傛灉椤圭洰瑕佺户缁悜鈥淪tata 甯哥敤鍛戒护鍙洿鎺ヨ縼绉烩€濇帹杩涳紝杩欎竴灞備笉鑳介暱鏈熺己澶便€?
## 2. 鎬荤洰鏍?
鏈疆鎶?factor grammar 浠庡綋鍓?Phase C 鍐嶆帹杩涗竴姝ワ紝褰㈡垚涓€涓洿鎺ヨ繎 Stata 甯哥敤 `fvvarlist` 鐨?**Phase D 瀛愰泦**銆?
鏈疆鑷冲皯瀹炵幇锛?
- 闄愬畾鑼冨洿鍐呯殑涓夐樁 `##`
- 闄愬畾鑼冨洿鍐呯殑鎷彿缂╁啓
- 鍦ㄦ牳蹇?wrapper 鍛戒护涓殑鐪熷疄鍙敤鎬?- 鎵嬪伐灞曞紑绛変环娴嬭瘯涓?Stata dual-run 璇佹嵁

鏈疆浠嶇劧涓嶈拷姹傚畬鏁?Stata `fvvarlist` 缁堟€侊紝浣嗗繀椤绘妸杩欏嚑涓珮浠峰€肩己鍙ｅ仛鍑烘潵銆?
## 3. 蹇呴』瀹屾垚鐨勫唴瀹?
### A. 鏀寔鏈夐檺鑼冨洿鍐呯殑涓夐樁 `##`

鎵╁睍 `src/stataflow/compat/stata/factor_variables.py`锛岃嚦灏戞敮鎸侊細

- `x1##x2##x3`
- `i.g##c.x1##c.x2`
- `i.g1##i.g2##c.x1`

璇箟瑕佹眰锛?
- `##` 蹇呴』鍋氬畬鏁?factorial expansion
- 灞曞紑缁撴灉瑕佷笌 Stata 涓€鑷村湴鍖呭惈锛?  - 涓绘晥搴?  - 浜岄樁浜や簰
  - 涓夐樁浜や簰
- 瑁稿彉閲忎粛榛樿鎸夎繛缁彉閲?`c.` 瑙ｉ噴

鏈疆涓嶈姹傛敮鎸佷换鎰忔洿楂橀樁浜や簰锛涘洓闃跺強浠ヤ笂蹇呴』缁х画鏄庣‘鎷掔粷銆?
### B. 鏀寔鏈夐檺鑼冨洿鍐呯殑鎷彿缂╁啓

鑷冲皯鏀寔锛?
- `c.(x1 x2)`
- `i.(g1 g2)`
- `c.(x1 x2)##i.g`
- `i.(g1 g2)##c.x1`

璇箟瑕佹眰锛?
- 鎷彿缂╁啓瑕佸湪 wrapper 灞傚厛灞曞紑锛屽啀璧扮幇鏈?factor parser
- 灞曞紑缁撴灉蹇呴』涓庢墜宸ュ啓鍑虹殑绛変环寮忎竴鑷?- 涓嶅厑璁?silent ignore

### C. 鎺ュ埌楂橀 wrapper 鍛戒护

鑷冲皯鎺ュ埌锛?
- `regress`
- `reghdfe`
- `ivreghdfe`
- `logit` 鎴?`poisson`

骞堕獙璇侊細

- `reghdfe(..., absorb="firm year")` 涓?factor expansion 鍏卞瓨
- 涓绘晥搴斿彲琚?absorb 鎺夋椂锛屼粛淇濈暀鏈?variation 鐨勪氦浜掗」

### D. 鏇存柊鐮旂┒鏂囨。涓庢敮鎸佺煩闃?
鑷冲皯鏇存柊锛?
- `docs/research/factor-variable-semantics.md`
- `docs/command-support-matrix/regress.md`
- `docs/command-support-matrix/reghdfe.md`
- `docs/command-support-matrix/ivreghdfe.md`
- `docs/command-support-matrix/logit.md` 鎴?`poisson.md`

蹇呴』鏄庣‘鍖哄垎锛?
- 鏈疆鏂版敮鎸佺殑涓夐樁 / 鎷彿缂╁啓璇箟
- 缁х画鏈敮鎸佺殑璇硶
- 鏄庣‘鎷掔粷瑙勫垯

## 4. 娴嬭瘯瑕佹眰

### A. 鍗曞厓娴嬭瘯

鎵╁睍 `tests/test_factor_variables.py`锛岃嚦灏戣鐩栵細

- `x1##x2##x3` 灞曞紑缁撴灉
- `i.g##c.x1##c.x2` 灞曞紑缁撴灉
- `c.(x1 x2)` 涓庢墜宸ュ睍寮€绛変环
- `i.(g1 g2)##c.x1` 涓庢墜宸ュ睍寮€绛変环
- 鍥涢樁浜や簰缁х画鎶?`ValueError`
- 鏈敮鎸佺殑澶嶆潅鎷彿缁勫悎缁х画鎶?`ValueError`

### B. 鎵嬪伐灞曞紑绛変环娴嬭瘯

鑷冲皯瑕嗙洊锛?
- `regress(..., x=["x1##x2##x3"])`
- `reghdfe(..., x=["i.g##c.x1##c.x2"], absorb="firm year")`
- `ivreghdfe(..., x=["i.(g1 g2)##c.x1"], absorb="firm year")`

### C. Stata dual-run

鑷冲皯鏂板骞堕€氳繃锛?
- `regress y x1##x2##x3`
- `reghdfe y i.g##c.x1##c.x2, absorb(firm year)`
- 涓€涓?`ivreghdfe` 鎴栭潪绾挎€у懡浠ょ殑鎷彿缂╁啓 case

### D. 鍏ㄩ噺楠岃瘉

瀹屾垚鍚庤嚦灏戝洖鎶ワ細

```powershell
python -m pytest tests/test_factor_variables.py -v
python -m pytest tests/test_compat_stata_linear.py tests/test_compat_stata_hdfe.py tests/test_compat_stata_iv.py tests/test_compat_stata_glm.py -v
python -m pytest tests -v
```

## 5. 绂佹浜嬮」

鏈疆涓嶈椤烘墜鍋氾細

- 鏃堕棿搴忓垪绠楀瓙 `L.` / `F.` / `D.`
- 浜旈樁鍙婁互涓婁氦浜?- 鍏ㄩ噺 Stata `fvvarlist` 缁堟€?- 涓?factor grammar 鏃犲叧鐨勪及璁″櫒鎵╁睍

## 6. 瀹屾垚鏍囧噯

鏈疆閫氳繃鐨勬渶浣庢爣鍑嗭細

- 涓夐樁 `##` 鐨勬渶灏忓彲鐢ㄥ瓙闆嗚繘鍏?wrapper 灞?- 鎷彿缂╁啓鐨勬渶灏忓彲鐢ㄥ瓙闆嗚繘鍏?wrapper 灞?- `regress` / `reghdfe` / `ivreghdfe` / 鑷冲皯涓€涓潪绾挎€у懡浠ゅ叿澶囩湡瀹炶瘉鎹?- 鏂囨。銆佹敮鎸佺煩闃点€佹祴璇曘€佹姤鍛婂悓姝ヤ竴鑷?
濡傛灉 Claude Code 鍦ㄦ姤鍛婁腑鎶婃湰杞じ澶ф垚鈥滃畬鏁?`fvvarlist` 宸插畬鎴愨€濓紝瑙嗕负鏈畬鎴愩€?