# 涓嬩竴杞换鍔″寘 002 杩斿伐锛欻DFE Source Map 涓€鑷存€ф敹鍙?
## 鍩烘湰淇℃伅

- 浠诲姟鍚嶇О锛欻DFE Source Map 涓€鑷存€ф敹鍙?- 鎵€灞為樁娈碉細寮€婧愬垵鐗堜笅涓€杞?- 鏉ユ簮锛氫换鍔″寘 002 琚?Codex 閫€鍥炲悗鐨勫畾鍚戣繑宸?- 浼樺厛绾э細P0
- 鎵ц浜猴細Claude Code
- 瀹℃煡浜猴細Codex

## 杩斿伐鐩爣

鏈杩斿伐 **涓嶆柊澧炲姛鑳借寖鍥?*锛屽彧鍋氫竴浠朵簨锛?
鎶?`reghdfe`銆乣ivreghdfe`銆乣ppmlhdfe` 涓変唤 source-to-python mapping 鏂囨。涓庡綋鍓嶇湡瀹炲疄鐜般€亀rapper 鏆撮湶闈€佹祴璇曡瘉鎹摼瀹屽叏瀵归綈銆?
## 蹇呰鏉愭枡

1. `workspace/current-task/review-next-round-package-002-codex.md`
2. `docs/research/reghdfe-source-map.md`
3. `docs/research/ivreghdfe-source-map.md`
4. `docs/research/ppmlhdfe-source-map.md`
5. `src/stataflow/compat/stata/hdfe.py`
6. `src/stataflow/compat/stata/iv.py`
7. `src/stataflow/estimators/absorbing_ols.py`
8. `src/stataflow/estimators/iv.py`
9. `src/stataflow/estimators/ppmlhdfe.py`
10. `tests/test_hdfe_synthetic.py`

## 蹇呴』瀹屾垚鐨勫伐浣?
### A. 淇涓変唤 source map 鐨勮繃鏈熺粨璁?
蹇呴』淇鑷冲皯浠ヤ笅鐭涚浘锛?
- `reghdfe-source-map.md` 涓叧浜?`vce(robust)` 鈥滃皻鏈疄鐜扳€濈殑鏃х粨璁?- `ivreghdfe-source-map.md` 涓叧浜?`vce(robust)` 鈥滃皻鏈敮鎸佲€濈殑鏃х粨璁?- `ppmlhdfe-source-map.md` 涓叧浜?`offset/exposure` 鈥滄湭鏆撮湶/鏈疄鐜扳€濈殑鏃х粨璁?
### B. 涓烘瘡浠?source map 澧炲姞缁熶竴缁撴瀯

姣忎唤鏂囨。閮藉繀椤诲崟鐙鍔?3 涓皬鑺傦細

1. `宸插疄鐜颁笖鏈夋槑纭簮鐮佷緷鎹甡
2. `宸插疄鐜帮紝浣嗗睘浜?Phase A 鐨勭瓑浠峰疄鐜癭
3. `鏈疄鐜版垨鏄惧紡鎷掔粷`

涓嶈兘鍐嶆妸鈥滃凡瀹炵幇浣嗗彧鏄渶灏忓瓙闆嗏€濆拰鈥滃皻鏈疄鐜扳€濇贩鍦ㄤ竴璧枫€?
### C. 鏇存柊鎵ц鎶ュ憡

`workspace/current-task/REPORT.md` 蹇呴』锛?
- 鏇存柊涓轰笌鏈€鏂版祴璇曠姸鎬佷竴鑷?- 涓嶅啀淇濈暀 `400/401 passed` 绛夋棫缁撹
- 鏄庣‘鍐欐竻锛氳繖娆¤繑宸ュ彧鏀跺彛鏂囨。涓庤瘉鎹摼锛屼笉鏂板绠楁硶鑼冨洿

## 鏄庣‘涓嶅仛

- 涓嶆柊澧?HDFE 鍔熻兘
- 涓嶆墿鏂扮殑鍙傛暟闈?- 涓嶄慨鏀?backlog 瑙勫垝
- 涓嶆彁鍓嶅紑濮嬩换鍔″寘 003

## 楠屾敹鏍囧噯

- [ ] 涓変唤 source map 涓嶅啀鍖呭惈涓庡綋鍓嶅疄鐜扮煕鐩剧殑鏃х粨璁?- [ ] 姣忎唤 source map 閮芥湁缁熶竴鐨勪笁娈靛紡鏀跺彛缁撴瀯
- [ ] `REPORT.md` 涓庢渶鏂版祴璇曠粨鏋滀竴鑷?- [ ] `pytest tests/test_hdfe_synthetic.py -v` 閫氳繃
- [ ] `pytest tests -v` 閫氳繃
