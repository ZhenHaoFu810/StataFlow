# 瀹¤鍚庝换鍔″寘 003 杩斿伐锛氶殣寮忚繛缁彉閲?factor 璇箟

## 1. 杩斿伐鐩爣

鏈杩斿伐鍙В鍐充竴涓樆濉為棶棰橈細

璁?Stata 甯哥敤鐨?*瑁歌繛缁彉閲?*浜や箻璇箟鐪熸鍙敤锛岃€屼笉鏄繀椤诲啓鎴愭樉寮?`c.` 鎵嶈兘閫氳繃銆?
鏈€浣庨渶瑕佸榻愮殑 Stata 璇箟锛?
- `x1#x2` 绛変环浜?`c.x1#c.x2`
- `x1##x2` 绛変环浜?`c.x1##c.x2`

杩欑偣瀵?`reghdfe y x1##x2, absorb(firm year)` 涔嬬被鍛戒护鏄垰闇€锛屼笉鑳界户缁姹傜敤鎴锋敼鍐欐垚鏄惧紡 `c.`銆?
## 2. 蹇呴』瀹屾垚鐨勫唴瀹?
### A. parser 璇箟淇

鏇存柊 `src/stataflow/compat/stata/factor_variables.py`锛?
- 涓嶅啀鎶婅８鍙橀噺鍙備笌 `#` / `##` 涓€寰嬬‖鎷掔粷
- 瀵硅繛缁彉閲忓満鏅仛 Stata 瀵归綈锛?  - `x1#x2` 鈫?`c.x1#c.x2`
  - `x1##x2` 鈫?`c.x1##c.x2`

### B. mixed 鍐欐硶缁熶竴

鑷冲皯鏄庣‘骞跺疄鐜颁互涓嬫贩鍚堟儏褰㈢殑缁熶竴绛栫暐锛?
- `x1#c.x2`
- `c.x1#x2`
- `x1##c.x2`
- `c.x1##x2`
- `x1#i.g`
- `i.g#x1`
- `x1##i.g`
- `i.g##x1`

鍙互鎶婅８鍙橀噺瑙ｉ噴涓鸿繛缁彉閲忥紝浣嗗繀椤伙細

- 鍏ㄥ眬涓€鑷?- 鏂囨。鍐欐竻妤?- 缁撴灉涓庢樉寮?`c.` 鍐欐硶涓€鑷?
### C. 鏂板娴嬭瘯

鑷冲皯鏂板锛?
- `x1#x2` 涓?`c.x1#c.x2` 绛変环
- `x1##x2` 涓?`c.x1##c.x2` 绛変环
- `x1##i.g` 涓?`c.x1##i.g` 绛変环
- `reghdfe y x1##x2, absorb(firm year)` 鍙互杩愯骞朵笌鎵嬪伐灞曞紑涓€鑷?
### D. Stata dual-run

鑷冲皯鏂板涓€缁勶細

- `regress y x1##x2`
- `reghdfe y x1##x2, absorb(firm year)`

鑻ユ椂闂村厑璁革紝鍐嶈ˉ涓€涓潪绾挎€у懡浠ょ殑瑁稿彉閲?`##` case銆?
### E. 鏂囨。鍚屾

鑷冲皯鍚屾锛?
- `docs/research/factor-variable-semantics.md`
- `README.md`
- `docs/command-support-matrix/regress.md`
- `docs/command-support-matrix/reghdfe.md`
- `docs/command-support-matrix/ivreghdfe.md`
- `docs/command-support-matrix/ppmlhdfe.md`

蹇呴』鏄庣‘鍐欐竻锛?
- 瑁稿彉閲忓湪浜や箻璇硶閲岄粯璁ゆ寜杩炵画鍙橀噺瑙ｉ噴
- 鍝簺鍐欐硶浠嶆湭鏀寔

## 3. 涓嶈鍋氱殑浜?
鏈疆涓嶈椤烘墜鍋氾細

- `ib#.` / `b.` / `o.` 鍏ㄦ敮鎸?- 鏃堕棿搴忓垪绠楀瓙
- 涓夐樁鍙婁互涓婁氦浜?- 涓庢湰杩斿伐鏃犲叧鐨勭畻娉曟墿灞?
## 4. 楠岃瘉瑕佹眰

鑷冲皯鍥炴姤锛?
```powershell
python -m pytest tests/test_factor_variables.py -v
python -m pytest tests/test_hdfe_synthetic.py tests/test_compat_stata_iv.py tests/test_compat_stata_hdfe.py tests/test_compat_stata_glm.py -v
python -m pytest tests -v
```

## 5. 瀹屾垚鏍囧噯

鏈疆杩斿伐閫氳繃鐨勬渶浣庢爣鍑嗭細

- `x1#x2` 涓?`x1##x2` 宸茶鎺ュ彈骞舵寜 Stata 杩炵画鍙橀噺璇箟澶勭悊
- `reghdfe y x1##x2, absorb(firm year)` 宸插彲鐢?- 娣峰悎瑁稿彉閲?鏄惧紡 `c.` / `i.` 鍐欐硶绛栫暐缁熶竴
- 鏂囨。涓庢祴璇曞悓姝ヤ竴鑷?