# Wave 3 鏈€缁堣繑宸ワ細`PPMLHDFE` 鐨?z 鎺ㄦ柇涓庡瓧娈佃鐩?
## 鍩烘湰淇℃伅

- 浠诲姟鍚嶇О锛歐ave 3 鏈€缁堣繑宸ワ細淇 `PPMLHDFE` 鐨?z 鎺ㄦ柇
- 鎵€灞炲懡浠ゆ棌锛歚Binary / Count`
- 浼樺厛绾э細P0
- 鎵ц浜猴細Claude Code
- 瀹℃煡浜猴細Codex

## 鑳屾櫙

Wave 3 绗簩娆¤繑宸ュ悗锛宍logit` / `probit` / `poisson` 鐨?`z` 鎺ㄦ柇宸蹭慨澶嶏紝`probit` 鐨?robust sandwich 涔熷凡淇锛宍PPMLHDFE` 鐨?`vce="ols"` 璇箟涔熷凡缁忔敹鍙ｃ€?
浣?`PPMLHDFE` 浠嶆湁鏈€鍚庝竴涓樆濉為棶棰橈細

- `p_value`
- `ci_low`
- `ci_high`

渚濈劧鎸?`t` 鍒嗗竷璁＄畻锛岃€屼笉鏄寜涓?Stata `ppmlhdfe` 涓€鑷寸殑 `z` 鍒嗗竷璁＄畻銆?
## 蹇呰鏂囦欢

1. `workspace/current-task/review-wave-3-rework-codex.md`
2. `docs/research/ppmlhdfe.md`
3. `docs/tasks/wave-3-rework-inference-semantics.md`
4. `workspace/current-task/REPORT.md`

## 鏈疆鐩爣

鍙仛 `PPMLHDFE` 鐨勬帹鏂垎甯冩敹鍙ｏ紝涓嶅仛浠讳綍鏂板姛鑳芥墿灞曘€?
### A. 淇 `PPMLHDFE` 鐨勬帹鏂垎甯?
鍦?`src/stataflow/estimators/ppmlhdfe.py` 涓細

- 绉婚櫎 `t` 鍒嗗竷鎺ㄦ柇
- 灏?`p_value` 鏀逛负鍩轰簬鏍囧噯姝ｆ€佸垎甯冭绠?- 灏?`ci_low` / `ci_high` 鏀逛负鍩轰簬鏍囧噯姝ｆ€佸垎甯冭绠?
淇濇寔鐜版湁 schema 涓嶅彉锛?
- `CoefficientRow.t_stat` 瀛楁鍚嶅彲浠ョ户缁繚鐣?- 浣嗗叾鍊煎疄闄呮槸 `beta / se`锛屽簲鎸?`z` 缁熻閲忚В閲?
### B. 琛ヤ笂 `PPMLHDFE` 瀛楁绾ф祴璇曡鐩?
蹇呴』涓?`PPMLHDFE` 鏂板瀛楁绾ф柇瑷€锛岃嚦灏戣鐩栵細

- `p_value`
- `ci_low`
- `ci_high`

寤鸿鍦ㄤ互涓嬫枃浠朵腑琛ユ祴璇曪細

- `tests/golden/test_w3_ppmlhdfe_basic.py`
- `tests/golden/test_w3_ppmlhdfe_real_gravity.py`

娴嬭瘯瑕佹眰锛?
- 鐢?Stata 杩斿洖鐨?`beta` 鍜?`se`锛屾寜姝ｆ€佸垎甯冨弽鎺ㄦ湡鏈涘€?- 涓?Python 缁撴灉瀵硅薄閲岀殑瀛楁閫愰」姣旇緝

## 鍏佽淇敼鐨勬枃浠?
- `src/stataflow/estimators/ppmlhdfe.py`
- `tests/golden/test_w3_ppmlhdfe_basic.py`
- `tests/golden/test_w3_ppmlhdfe_real_gravity.py`
- 蹇呰鏃跺皯閲忔洿鏂?`docs/research/ppmlhdfe.md`
- `workspace/current-task/REPORT.md`

## 绂佹浜嬮」

- 涓嶈鎵╁睍鍒?`nbreg`銆乣zip`銆乣zinb`
- 涓嶈淇敼 `logit` / `probit` / `poisson` 宸查€氳繃閮ㄥ垎
- 涓嶈鎵╁睍 `ppmlhdfe` 鐨勬柊閫夐」
- 涓嶈鎶婃湭楠岃瘉瀛楁鍐欐垚鈥滃彲鎺ュ彈宸紓鈥?
## 寮哄埗楠岃瘉鍛戒护

```bash
python -m pytest tests/golden/test_w3_ppmlhdfe_basic.py -v
python -m pytest tests/golden/test_w3_ppmlhdfe_real_gravity.py -v
python -m pytest tests/golden/test_w3_ppmlhdfe_cluster.py -v
python -m pytest tests -v
```

濡傛灉鏂板浜嗘柊鐨?`PPMLHDFE` 娴嬭瘯鏂囦欢锛屽繀椤诲湪鎶ュ憡涓垪鍑哄苟瀹為檯杩愯銆?
## 鍥炴姤瑕佹眰

鎶ュ憡蹇呴』鏄庣‘鍐欐竻锛?
1. `PPMLHDFE` 鐨?`p_value` / `ci` 鐜板湪濡備綍鎸?`z` 鍒嗗竷璁＄畻
2. 鏂板浜嗗摢浜涙祴璇曟潵瑕嗙洊涔嬪墠閬楁紡鐨勫瓧娈?3. 鍝簺瀛楁鏄洿鎺ユ嬁 Stata 鐨?`beta` / `se` 鍙嶆帹鐨?4. 鍏ㄩ噺娴嬭瘯缁撴灉

## 閫氳繃鏍囧噯

鍙湁鍚屾椂婊¤冻浠ヤ笅鏉′欢锛孋odex 鎵嶄細鏀捐 Wave 3锛?
- `PPMLHDFE` 涓嶅啀浣跨敤 `t` 鍒嗗竷杩涜鎺ㄦ柇
- `PPMLHDFE` 鐨?`p_value` / `ci_low` / `ci_high` 琚粍閲戞祴璇曟樉寮忚鐩?- `python -m pytest tests -v` 鍏ㄧ豢
- `REPORT.md` 涓嶅啀杩囨棭瀹ｇО Wave 3 瀹屾垚
