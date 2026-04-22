# Wave 3 Rework锛歚Binary / Count` 鎺ㄦ柇璇箟杩斿伐

## 鍩烘湰淇℃伅

- 浠诲姟鍚嶇О锛歐ave 3 杩斿伐锛氫慨姝?MLE 鎺ㄦ柇鍒嗗竷銆乸robit sandwich score銆乣ppmlhdfe` VCE 璇箟
- 鎵€灞炲懡浠ゆ棌锛歚Binary / Count`
- 浼樺厛绾э細P0
- 鎵ц浜猴細Claude Code
- 瀹℃煡浜猴細Codex

## 杩斿伐鑳屾櫙

Wave 3 褰撳墠 **娴嬭瘯鍏ㄧ豢浣嗕笉浜堟斁琛?*銆傞樆濉炲師鍥犱笉鏄郴鏁颁笉瀵癸紝鑰屾槸鎺ㄦ柇灞傜粺璁″彛寰勫瓨鍦ㄩ敊璇細

1. `logit` / `probit` / `poisson` 鎶?MLE 鎺ㄦ柇鍋氭垚浜?`t` 鍒嗗竷锛岃€屼笉鏄?Stata 鐨?`z` 鍒嗗竷銆?2. `probit` 鐨?robust / cluster meat 娌℃湁浣跨敤姝ｇ‘鐨?score銆?3. `PPMLHDFE.fit(vce="ols")` 鐨勫疄鐜拌涔変笌鍛藉悕涓嶄竴鑷淬€?
璇︾粏闂瑙侊細

- `workspace/current-task/review-wave-3-codex.md`

## 蹇呰鏂囨。

1. `workspace/current-task/review-wave-3-codex.md`
2. `docs/research/logit.md`
3. `docs/research/probit.md`
4. `docs/research/poisson.md`
5. `docs/research/ppmlhdfe.md`
6. `docs/tasks/wave-3-full-package-binary-count.md`

## 浠诲姟鐩爣

### A. 淇 MLE 鎺ㄦ柇鍒嗗竷

瀵逛互涓嬪懡浠わ細

- `logit`
- `probit`
- `poisson`

灏嗭細

- `p_value`
- `ci_low`
- `ci_high`

鏀逛负鍩轰簬 **鏍囧噯姝ｆ€佸垎甯?* 璁＄畻锛岃€屼笉鏄?`t` 鍒嗗竷銆?
### B. 淇 `probit` 鐨?robust / cluster score

鍦?`Probit._compute_vce()` 涓細

- robust meat 蹇呴』浣跨敤姝ｇ‘鐨?probit 瑙傛祴寰楀垎
- cluster meat 蹇呴』浣跨敤鎸?cluster 鑱氬悎鐨勬纭?probit score

涓嶅緱缁х画浣跨敤 `X' (y - mu)` 鐨勭畝鍖栧舰寮忋€?
### C. 鏀跺彛 `ppmlhdfe` 鐨?`vce="ols"` 璇箟

浜岄€変竴锛屼絾蹇呴』鏄庣‘瀹屾垚锛?
1. 涓ユ牸瀹炵幇 `vce="ols"` 鐨?conventional VCE锛涙垨
2. 閲嶆瀯 API / 鏂囨。 / 鍏冩暟鎹紝浣块粯璁ょǔ鍋ヨ涔変笌 `vce="ols"` 涓嶅啀娣锋穯銆?
涓嶅厑璁哥户缁繚鎸佲€滃悕瀛楀彨 ols锛屼唬鐮佽窇 robust鈥濈殑鐘舵€併€?
## 鍏佽淇敼鐨勬枃浠?
- `src/stataflow/estimators/glm.py`
- `src/stataflow/estimators/ppmlhdfe.py`
- `src/stataflow/results/result.py`
- `tests/golden/` 涓?Wave 3 鐩稿叧娴嬭瘯
- 蹇呰鐨勬祴璇曞伐鍏锋枃浠?- `docs/research/ppmlhdfe.md`
- `workspace/current-task/REPORT.md`

## 蹇呴』鏂板鎴栬ˉ寮虹殑娴嬭瘯

鑷冲皯鏂板浠ヤ笅涓€绫伙細

- `probit` 鐨?robust 鎴?cluster golden test
- `logit/probit/poisson` 鐨?`p_value` / `ci` 瀛楁鏂█
- `ppmlhdfe` 鐨?`vcetype` / VCE 璇箟鏂█

寤鸿涓夌被閮借ˉ銆?
## 寮哄埗楠岃瘉鍛戒护

```bash
python -m pytest tests/golden/test_w3_logit_basic.py -v
python -m pytest tests/golden/test_w3_logit_real.py -v
python -m pytest tests/golden/test_w3_probit_basic.py -v
python -m pytest tests/golden/test_w3_probit_real.py -v
python -m pytest tests/golden/test_w3_poisson_basic.py -v
python -m pytest tests/golden/test_w3_poisson_real.py -v
python -m pytest tests/golden/test_w3_ppmlhdfe_basic.py -v
python -m pytest tests/golden/test_w3_ppmlhdfe_cluster.py -v
python -m pytest tests/golden/test_w3_ppmlhdfe_real_gravity.py -v
python -m pytest tests -v
```

濡傛柊澧炴柊鐨?golden 娴嬭瘯鏂囦欢锛屽繀椤诲湪鍥炴姤涓垪鍑哄苟瀹為檯杩愯銆?
## 鍥炴姤瑕佹眰

鍥炴姤蹇呴』鏄庣‘璇存槑锛?
1. MLE 鍛戒护鐨?`z` 鍒嗗竷鎺ㄦ柇濡備綍瀹炵幇
2. `probit` score 鐨勫叕寮忎笌瀹炵幇瀵瑰簲鍏崇郴
3. `ppmlhdfe` 鏈€缁堥€夋嫨浜嗗摢绉?`vce="ols"` 璇箟鏀跺彛鏂规
4. 鍝簺娴嬭瘯鏄繖娆℃柊澧炵殑锛岃鐩栦簡鍝簺涔嬪墠鏈鐩栫殑瀛楁
5. 鍏ㄩ噺娴嬭瘯缁撴灉

## 閫氳繃鏍囧噯

鍙湁鍚屾椂婊¤冻浠ヤ笅鏉′欢锛孋odex 鎵嶄細閲嶆柊鑰冭檻鏀捐 Wave 3锛?
- `logit` / `probit` / `poisson` 鐨勬帹鏂垎甯冩敼涓?`z`
- `probit` 鐨?robust / cluster sandwich 瀹炵幇涓庣爺绌舵。妗堜竴鑷?- `ppmlhdfe` 鐨?`vce="ols"` 鍛藉悕涓庡疄鐜颁笉鍐嶅啿绐?- 鏂板娴嬭瘯纭疄瑕嗙洊浜嗚繖娆″彂鐜扮殑闂
- 鍏ㄩ噺鍥炲綊娴嬭瘯閫氳繃
