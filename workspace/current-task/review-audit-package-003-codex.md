# Codex Review: 瀹¤鍚庝换鍔″寘 003

## 缁撹

**涓嶉€氳繃锛岄渶瑕佽繑宸ャ€?*

## fresh verification

宸茬嫭绔嬪璺戯細

```powershell
python -m pytest tests/test_factor_variables.py tests/test_hdfe_synthetic.py tests/test_compat_stata_iv.py tests/test_compat_stata_hdfe.py tests/test_compat_stata_glm.py -v
python -m pytest tests -v
```

缁撴灉锛?
- 涓撻」娴嬭瘯锛歚69 passed`
- 鍏ㄩ噺娴嬭瘯锛歚579 passed`

娴嬭瘯鍩虹嚎鏄共鍑€鐨勶紝浣嗚繖涓嶈冻浠ユ斁琛屻€?
## 闃诲鐐?
### 1. 瑁稿彉閲忎氦涔樿涔変笌鐢ㄦ埛鏄庣‘瑕佹眰涓嶄竴鑷?
鐢ㄦ埛宸茬粡鏄庣‘鎻愬嚭浠ヤ笅 Stata 甯哥敤鍐欐硶搴旇鏀寔锛?
```stata
reghdfe y x1##x2, absorb(firm year)
```

褰撳墠瀹炵幇鍗寸粺涓€鎶婅８鍙橀噺鍙備笌鐨?`#` / `##` 鍐欐硶纭嫆缁濓細

```text
ValueError: Bare variables are not allowed inside factor interactions; explicitly use c. or i. for term: x1##x2
```

杩欐剰鍛崇潃褰撳墠搴撹櫧鐒舵敮鎸佷簡 `c.x1##c.x2`锛屼絾浠嶇劧**涓嶆敮鎸佺敤鎴锋槑纭偣鍚嶇殑鍛戒护灞傚啓娉?*銆傚湪 Stata 涓紝`x1##x2` 鐨勯粯璁よ涔夊氨鏄繛缁彉閲忓叏鍥犲瓙灞曞紑锛涘綋鍓嶅疄鐜版妸瀹冨綋鎴愰敊璇紝杩欎笉鑳芥帴鍙椼€?
杩欎笉鏄枃妗ｆ帾杈為棶棰橈紝鑰屾槸瀹為檯鍏叡鍛戒护鎺ュ彛涓嶇鍚堢洰鏍囪涔夈€?
### 2. 鎶ュ憡鎶娾€滄槑纭嫆缁濊８鍙橀噺浜や箻鈥濆啓鎴愰樁娈垫€у畬鎴愶紝涓嶅彲鎺ュ彈

[workspace/current-task/REPORT.md](</D:/OneDrive - SAIF/PhD3/StataFlow/workspace/current-task/REPORT.md>) 鎶娾€滆８鍙橀噺鍙備笌 `#` / `##` 鏄庣‘鎷掔粷鈥濆啓鎴愪簡鏈疆鐨勭粺涓€绛栫暐涓庡畬鎴愰」銆?
浣嗕粠褰撳墠椤圭洰鐩爣鍜岀敤鎴疯姹傜湅锛岃繖涓嶆槸鍙帴鍙楃殑浜у搧杈圭晫锛岃€屾槸灏氭湭瀹屾垚鐨勭己鍙ｃ€傛姤鍛婂湪杩欎竴鐐逛笂鐨勭粨璁轰笉鑳戒綔涓烘斁琛屼緷鎹€?
## 涓轰粈涔堟祴璇曞叏缁夸粛鐒朵笉鑳介€氳繃

鍥犱负褰撳墠娴嬭瘯鐭╅樀宸茬粡榛樿鎺ュ彈浜嗏€滆８鍙橀噺浜や箻蹇呴』鎷掔粷鈥濊繖涓骇鍝佸喅绛栵紱涔熷氨鏄锛屾祴璇曢獙璇佺殑鏄?*瀹炵幇鏄惁蹇犱簬褰撳墠浠ｇ爜鍐崇瓥**锛屽苟娌℃湁楠岃瘉杩欎釜鍐崇瓥鏈韩鏄惁绗﹀悎椤圭洰鐩爣涓庣敤鎴疯姹傘€?
## 杩斿伐瑕佹眰

涓嬩竴杞繑宸ュ彧鑱氱劍杩欎竴浠朵簨锛?
- 鏀寔 Stata 涓８杩炵画鍙橀噺鐨?`#` / `##` 璇箟

鏈€浣庤姹傦細

- `x1#x2` 绛変环浜?`c.x1#c.x2`
- `x1##x2` 绛変环浜?`c.x1##c.x2`
- `x1#c.x2`銆乣c.x1#x2`銆乣x1##i.g`銆乣i.g##x1` 绛夋贩鍚堝啓娉曠粰鍑虹粺涓€銆佸彲瑙ｉ噴銆丼tata 瀵归綈鐨勫鐞?- 涓嶈兘鐮村潖褰撳墠宸茬粡閫氳繃鐨?`i.` / `c.` 鏄惧紡璇箟

閫氳繃鍓嶏紝涓嶅簲涓嬫斁涓嬩竴姝ュぇ浠诲姟銆?