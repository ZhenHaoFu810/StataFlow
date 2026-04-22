# 瀹¤鍚庝换鍔″寘 004锛氬洜瀛愬彉閲?Phase C 涓?base-level / omitted-level 璇箟

## 1. 浠诲姟鑳屾櫙

浠诲姟鍖?002 涓?003 宸茬粡鎶婁互涓嬮珮棰?factor 璇箟鎺ュ叆 wrapper 灞傦細

- `c.x1#c.x2`
- `c.x1##c.x2`
- `i.g1#i.g2`
- `i.g1##i.g2`
- `i.g1#c.x1`
- `i.g1##c.x1`
- `c.x1##i.g1`
- `x1##x2`
- `x1##i.g`

杩欏凡缁忚冻浠ヨ鐩栧ぇ閲忓父瑙佸疄璇佸洖褰掑啓娉曪紝浣嗗綋鍓?factor grammar 浠嶆湁涓€涓緢鏄庢樉鐨勪笅涓€闃舵缂哄彛锛?
- `ib#.` / `b.` / `o.` 鐨?base-level / omitted-level 璇箟浠嶆湭瀹炵幇

杩欐剰鍛崇潃鐢ㄦ埛杩樹笉鑳芥洿绮剧‘鍦版帶鍒讹細

- 鍝釜鍒嗙被姘村钩浣滀负鍩哄噯缁?- 鍝簺姘村钩琚樉寮忕渷鐣?- 鏌愪簺 Stata `fvvarlist` 缁撴灉鍒楀悕涓庡鐓ч€昏緫

濡傛灉椤圭洰瑕佺户缁€艰繎鈥淪tata 甯哥敤鍛戒护鐪熷疄杩佺Щ浣撻獙鈥濓紝杩欎竴灞備笉鑳介暱鏈熺己澶便€?
## 2. 鎬荤洰鏍?
鏈疆鎶?factor grammar 浠庡綋鍓?Phase B 鍐嶆帹杩涗竴姝ワ紝閲嶇偣瀹炵幇锛?
- `ib#.` / `b.` / `o.` 鐨勬渶灏忓彲鐢ㄨ涔?- 鏇存槑纭殑 base/omitted level 鍒楀懡鍚嶄笌缁撴灉瀵硅薄琛屼负
- 鍦?`regress`銆乣reghdfe`銆佽嚦灏戜竴涓潪绾挎€у懡浠や腑瀹屾垚 dual-run 璇佹嵁

鏈疆浠嶇劧涓嶈拷姹傚畬鏁?`fvvarlist` 缁堟€侊紝浣嗚鎶?**鏈€鏍稿績鐨勫熀鍑嗙粍/鐪佺暐缁勬帶鍒惰涔?* 鍋氬嚭鏉ャ€?
## 3. 蹇呴』瀹屾垚鐨勫唴瀹?
### A. parser 鏀寔 base / omitted level 璇硶

鎵╁睍 `src/stataflow/compat/stata/factor_variables.py`锛岃嚦灏戞敮鎸侊細

- `ib2.g`
- `ib3.g`
- `b2.g`
- `o2.g`

闇€瑕佹槑纭細

- `ib2.g` / `b2.g` 濡備綍鎸囧畾鍩哄噯缁?- `o2.g` 濡備綍鎸囧畾棰濆鐪佺暐姘村钩
- 濡傛灉鎸囧畾鐨?level 涓嶅瓨鍦紝蹇呴』鎶ユ槑纭敊璇?
### B. 涓庣幇鏈?`i.g` 璇箟鏁村悎

瑕佹眰锛?
- `i.g` 浠嶉粯璁ゅ彇绗竴鎺掑簭姘村钩涓哄熀鍑嗙粍
- `ib#.g` / `b#.g` 浼氳鐩栭粯璁ゅ熀鍑嗙粍
- `o#.g` 鍦ㄧ敓鎴愰」鏃舵纭渷鐣ュ搴旀按骞?- 缁撴灉鍒楀悕淇濇寔 Stata 椋庢牸

### C. 鎺ュ叆楂橀 wrapper 鍛戒护

鑷冲皯鎺ュ叆锛?
- `regress`
- `reghdfe`
- `ivreghdfe`
- `logit` 鎴?`poisson`

### D. 鏇存柊鐮旂┒涓庢敮鎸佺煩闃?
鑷冲皯鏇存柊锛?
- `docs/research/factor-variable-semantics.md`
- `docs/command-support-matrix/regress.md`
- `docs/command-support-matrix/reghdfe.md`
- `docs/command-support-matrix/ivreghdfe.md`
- `docs/command-support-matrix/logit.md` 鎴?`poisson.md`
- `README.md`锛堝鏈夊繀瑕侊級

鏂囨。蹇呴』鏄庣‘鍖哄垎锛?
- 宸叉敮鎸侊細`i.`銆乣ib#.`銆乣b#.`銆乣o#.`
- 浠嶆湭鏀寔锛氭洿澶嶆潅 `fvvarlist` 鍙樹綋銆佹椂闂村簭鍒楃畻瀛愩€佷笁闃朵氦浜?
## 4. 娴嬭瘯瑕佹眰

### A. 鍗曞厓娴嬭瘯

鏂板鎴栨墿灞?`tests/test_factor_variables.py`锛岃嚦灏戣鐩栵細

- `i.g` 榛樿鍩哄噯缁勮涓?- `ib2.g` 瑕嗙洊榛樿鍩哄噯缁?- `b2.g` 涓?`ib2.g` 绛変环
- `o2.g` 姝ｇ‘鐪佺暐姘村钩
- 涓嶅瓨鍦?level 鏃舵槑纭姤閿?
### B. 鎵嬪伐灞曞紑绛変环娴嬭瘯

鑷冲皯瑕嗙洊锛?
- `regress(..., x=["ib2.g##c.x1"])` 涓庢墜宸?dummy/interaction 灞曞紑涓€鑷?- `reghdfe(..., x=["ib2.g##c.x1"], absorb=...)` 涓庢墜宸ュ睍寮€涓€鑷?
### C. Stata dual-run

鑷冲皯鏂板骞堕€氳繃锛?
- `regress y ib2.g##c.x1`
- `reghdfe y ib2.g##c.x1, absorb(firm year)`
- 涓€涓潪绾挎€у懡浠ょ殑 `ib#.` / `b#.` case

### D. 鍏ㄩ噺楠岃瘉

瀹屾垚鍚庤嚦灏戝洖鎶ワ細

```powershell
python -m pytest tests/test_factor_variables.py -v
python -m pytest tests/test_compat_stata_linear.py tests/test_compat_stata_hdfe.py tests/test_compat_stata_iv.py tests/test_compat_stata_glm.py -v
python -m pytest tests -v
```

## 5. 绂佹浜嬮」

鏈疆涓嶈椤烘墜鍋氾細

- 鏃堕棿搴忓垪 factor 璇硶
- 涓夐樁鍙婁互涓婁氦浜?- 鍏ㄩ噺 `fvvarlist` 缁堟€?- 涓?factor grammar 鏃犲叧鐨勫叾浠栫畻娉曟墿灞?
## 6. 瀹屾垚鏍囧噯

鏈疆閫氳繃鐨勬渶浣庢爣鍑嗭細

- `ib#.` / `b#.` / `o#.` 鐨勬渶灏忚涔夊凡杩涘叆 wrapper 灞?- `regress` / `reghdfe` / 鑷冲皯涓€涓潪绾挎€у懡浠ゅ叿澶?dual-run 璇佹嵁
- 鏂囨。銆佹敮鎸佺煩闃点€佹祴璇曘€佹姤鍛婂悓姝ヤ竴鑷?
濡傛灉 Claude Code 鍦ㄦ姤鍛婇噷鎶婃湰杞じ澶ф垚鈥滃畬鏁?factor-variable grammar 宸插畬鎴愨€濓紝瑙嗕负鏈畬鎴愩€?