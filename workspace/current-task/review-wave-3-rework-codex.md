# Codex Review: Wave 3 Rework 浠嶆湭閫氳繃

## 缁撹

鏈疆 **涓嶉€氳繃**锛屼笉鑳借繘鍏ヤ笅涓€涓?wave銆?
铏界劧 Claude Code 鎶ュ憡鐨?Wave 3 杩斿伐娴嬭瘯鍏ㄩ儴閫氳繃锛岃€屼笖鎴戠嫭绔嬪璺?`python -m pytest tests -v` 涔熷緱鍒?`396 passed`锛屼絾 `PPMLHDFE` 浠嶇劧瀛樺湪涓€涓湭淇鐨勬帹鏂涔夐敊璇細`p_value` 鍜岀疆淇″尯闂寸户缁娇鐢?`t` 鍒嗗竷锛岃€屼笉鏄笌 Stata `ppmlhdfe` 涓€鑷寸殑 `z` 鍒嗗竷銆?
杩欎笉鏄€滃睍绀哄眰鈥濋棶棰橈紝鑰屾槸鍏紑缁撴灉瀵硅薄鐨勬暟瀛﹀彛寰勯敊璇€傜敱浜庡綋鍓?golden tests 娌℃湁瑕嗙洊 `PPMLHDFE` 鐨?`p_value` / `ci_low` / `ci_high`锛屾墍浠ユ祴璇曞叏缁垮苟涓嶈兘璇佹槑杩欓儴鍒嗗凡瀵归綈銆?
## 鐙珛澶嶆牳璇佹嵁

### 1. Claude Code 澹扮О鐨勬祴璇曠粨鏋?
- `python -m pytest tests -v`
- 缁撴灉锛歚396 passed`

### 2. Codex 鐙珛琛ュ厖鏍搁獙

鎴戦澶栬繍琛屼簡涓€涓洿鎺ユ鏌?`PPMLHDFE` 鎺ㄦ柇鍒嗗竷鐨勫皬鑴氭湰锛岀粨鏋滃涓嬶細

- `reported_p = 2.848779692143921e-07`
- `z_p = 9.444265525182516e-08`
- `t_p = 2.848779692143921e-07`

杩欒鏄庡綋鍓嶅疄鐜拌繑鍥炵殑 `p_value` 鏄庣‘绛変簬 `t` 鍒嗗竷缁撴灉锛岃€屼笉鏄?`z` 鍒嗗竷缁撴灉銆?
## 闃诲闂

### 1. `PPMLHDFE` 浠嶅湪浣跨敤 `t` 鍒嗗竷鎺ㄦ柇

- 鏂囦欢锛歚src/stataflow/estimators/ppmlhdfe.py`
- 闂锛?  - 浠嶇劧 `import scipy.stats.t as t_dist`
  - `p_values` 鐢?`t_dist.cdf(...)`
  - `ci_low` / `ci_high` 鐢?`t_dist.ppf(...)`

杩欎笌 Poisson PML / `ppmlhdfe` 鐨?MLE 鎺ㄦ柇鍙ｅ緞涓嶄竴鑷淬€?
### 2. 娴嬭瘯瑕嗙洊浠嶇劧缂哄け

褰撳墠鏂板鐨勮繑宸ユ祴璇曡鐩栦簡锛?
- `logit/probit/poisson` 鐨?`z` 鍒嗗竷鎺ㄦ柇
- `probit` robust VCE
- `ppmlhdfe` 鐨?`vcetype` / `vce="ols"` 璇箟

浣嗘病鏈夎鐩栵細

- `PPMLHDFE` 鐨?`p_value`
- `PPMLHDFE` 鐨?`ci_low`
- `PPMLHDFE` 鐨?`ci_high`

鎵€浠ヨ繖涓€杞€滄祴璇曞叏杩団€濆苟涓嶈冻浠ユ敮鎾?Wave 3 鏀捐銆?
### 3. 鎶ュ憡缁撹浠嶇劧杩囨棭

- 鏂囦欢锛歚workspace/current-task/REPORT.md`
- 闂锛?  - 浠嶇劧鎶?Wave 3 杩斿伐鍐欐垚鈥滃凡瀹屾垚鈥?  - 浣嗘牳蹇冩帹鏂瓧娈典粛鏈畬鍏ㄥ榻?
鍥犳杩欎唤鎶ュ憡涓嶈兘浣滀负瀹屾垚璇佹嵁銆?
## 杩斿伐瑕佹眰

Claude Code 涓嬩竴杞彧鍋氫竴浠朵簨锛?
- 淇 `PPMLHDFE` 鐨?`p_value` / `ci_low` / `ci_high` 鎺ㄦ柇鍒嗗竷锛屼娇鍏朵笌 Stata 鐨?`z` 鍙ｅ緞涓€鑷?
鍚屾椂蹇呴』琛ヤ笂瀵瑰簲娴嬭瘯锛?
- `tests/golden/test_w3_ppmlhdfe_basic.py`
- `tests/golden/test_w3_ppmlhdfe_real_gravity.py`

鑷冲皯瑕佹柊澧炲瓧娈电骇鏂█锛屾樉寮忛獙璇侊細

- `p_value`
- `ci_low`
- `ci_high`

## 褰撳墠鐘舵€?
- Wave 3锛?*浠嶆湭瀹屾垚**
- 涓嬩竴涓?wave锛?*涓嶅緱寮€濮?*
- 鏈疆鍙厑璁稿仛 `PPMLHDFE` 鎺ㄦ柇璇箟鏀跺彛锛屼笉寰楁墿灞曞埌鏂板懡浠?