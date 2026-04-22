# Codex Review: 涓嬩竴杞换鍔″寘 001

## 缁撹

涓嶉€氳繃锛屼笉鑳戒笅鏀句换鍔″寘 002銆?
## 闃诲鐐?
### 1. `reghdfe()` wrapper 鐨勫叕寮€鍛戒护璇箟浠嶇劧閿欒

褰撳墠锛?
- `from stataflow.compat.stata import reghdfe`
- 褰?`absorb` 浼犲叆鍗曚釜鍙橀噺瀛楃涓叉椂锛岃繑鍥炵粨鏋滃璞￠噷鐨?`res.model.command` 浠嶇劧鏄?`areg`

杩欒鏄?wrapper 鍙槸鎶婂弬鏁拌浆鍙戠粰浜?`AbsorbingOLS`锛屽苟娌℃湁鐪熸鎶婂澶栬涔夋敹鍙ｅ埌 `reghdfe`銆?
杩欎笉鏄睍绀哄眰闂锛岃€屾槸鍏叡 API 璇箟闂銆? 
濡傛灉鐢ㄦ埛璋冪敤鐨勬槸 `reghdfe()`锛岀粨鏋滃璞°€佹敮鎸佺煩闃靛拰鏂囨。閮戒笉搴旇鍐嶆毚闇叉垚 `areg`銆?
### 2. 鏀寔鐭╅樀涓殑璇佹嵁璺緞瀛樺湪铏氭瀯鎴栧け鐪?
褰撳墠鑷冲皯鍙戠幇锛?
- `docs/command-support-matrix/reghdfe.md` 寮曠敤浜嗕笉瀛樺湪鐨勶細
  - `tests/golden/test_p4_reghdfe_basic.py`
  - `tests/golden/test_p4_reghdfe_real_gravity.py`
- `docs/command-support-matrix/ppmlhdfe.md` 寮曠敤浜嗕笉瀛樺湪鐨勶細
  - `tests/golden/test_p8_ppmlhdfe_basic.py`
  - `tests/golden/test_p8_ppmlhdfe_real_gravity.py`
- `docs/command-support-matrix/csdid.md` 寮曠敤浜嗕笉瀛樺湪鐨勶細
  - `tests/golden/test_p9_csdid_basic.py`
  - `tests/golden/test_p9_csdid_real.py`
  - `research/vendor/stata_community/csdid/`

杩欐剰鍛崇潃褰撳墠鏀寔鐭╅樀涓嶆槸鍙潬璇佹嵁娓呭崟锛屽瓨鍦ㄢ€滃啓涓婂幓浜嗕絾浠撳簱閲屽苟娌℃湁鈥濈殑鎯呭喌銆?
瀵逛笅涓€杞紑婧愬垵鐗堟潵璇达紝杩欑被鏂囨。涓嶅彧鏄憰鐤碉紝鑰屾槸闃诲椤癸紝鍥犱负瀹冧細鐩存帴璇鍚庣画瀹炵幇涓庡澶栬鏄庛€?
### 3. 鎶ュ憡澶稿ぇ浜嗏€滄棤 core / wrapper 璇箟鍐茬獊鈥?
`REPORT.md` 鏄庣‘鍐欏埌锛?
- 鈥滄湭鍙戠幇鏁板璇箟鍐茬獊鈥?- 鈥滄棤 core / wrapper 璇箟鍐茬獊鈥?
浣嗗疄闄呬笂 `reghdfe()` 杩斿洖 `areg` 鍛戒护鏍囩杩欎竴鐐规湰韬氨鏄叕寮€璇箟鍐茬獊銆? 
鍥犳褰撳墠鎶ュ憡涓嶈兘浣滀负璇ヤ换鍔″寘瀹屾垚鐨勫彲淇¤瘉鎹€?
## 寤鸿杩斿伐鑼冨洿

鍙仛浠ヤ笅鏀跺彛锛屼笉瑕佹彁鍓嶈繘鍏ヤ换鍔″寘 002锛?
1. 淇 `reghdfe()` wrapper 鐨勫叕鍏辩粨鏋滆涔?   - 纭繚璋冪敤 `reghdfe()` 鏃讹紝缁撴灉瀵硅薄涓殑鍛戒护鏍囩銆佸厓鏁版嵁銆佹敮鎸佺煩闃佃娉曚竴鑷?   - 涓嶈兘鍥犱负鍐呴儴澶嶇敤 `AbsorbingOLS` 灏卞澶栨硠闇叉垚 `areg`

2. 鍏ㄩ潰鏍告煡 13 浠芥敮鎸佺煩闃?   - 鎵€鏈夋祴璇曡矾寰勫繀椤绘槸鐪熷疄瀛樺湪鐨勪粨搴撹矾寰?   - 鎵€鏈夋湰鍦版簮鐮侀暅鍍忚矾寰勫繀椤荤湡瀹炲瓨鍦?   - 涓嶅厑璁稿紩鐢ㄤ笉瀛樺湪鐨?case id 鎴栫洰褰?
3. 閲嶅啓 `REPORT.md` 涓殑缁撹娈?   - 涓嶅緱鍐嶅０绉扳€滄棤璇箟鍐茬獊鈥?   - 蹇呴』鎸変慨澶嶅悗鐨勫疄闄呯姸鎬佸洖鎶?
## 閲嶆柊楠屾敹鍓嶇殑鏈€浣庤姹?
- wrapper 涓撻」娴嬭瘯 fresh run 閫氳繃
- 鍏ㄩ噺娴嬭瘯 fresh run 閫氳繃
- `reghdfe()` 鍏叡璇箟 spot check 閫氳繃
- 鏀寔鐭╅樀鎶芥煡涓嶅啀鍑虹幇铏氭瀯璺緞
