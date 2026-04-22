# 瀹¤涓荤嚎浠诲姟鍖?002锛歚reghdfe` 瀹屾暣搴︽帹杩涳紙Phase B锛?
## 1. 鑳屾櫙

鏍规嵁 [docs/audit/next-development-plan.md](</D:/OneDrive - SAIF/PhD3/StataFlow/docs/audit/next-development-plan.md>)锛宍rdrobust` 杩涘叆涓荤嚎鍚庯紝涓嬩竴浼樺厛绾т笉鏄户缁í鍚戞墿璇硶锛岃€屾槸鎶婃渶鏈変环鍊肩殑 vendor 鍛戒护鍋氭繁銆佸仛鍏ㄣ€佸仛鍑嗐€?
褰撳墠 `reghdfe` 鐨勫璁＄粨璁烘槸锛?
- 宸叉湁楂樿川閲?Phase A 瀛愰泦
- 楂橀鍦烘櫙宸插彲鐢?- 浣嗚窛绂烩€滃畬鏁淬€佸叏闈€佹纭鐜?`reghdfe`鈥濅粛鏈夋槑鏄剧己鍙?
鏈疆浠诲姟鍙仛涓€浠朵簨锛?*鎶?`reghdfe` 浠庡綋鍓?Phase A 鎺ㄨ繘鍒版洿瀹屾暣鐨?Phase B**銆?
## 2. 鎬荤洰鏍?
鏈疆鑷冲皯鍦ㄤ互涓嬩笁涓柟鍚戜腑锛岀湡瀹炶ˉ榻愪竴鎵逛箣鍓嶆槑纭己澶辩殑 `reghdfe` 鑳藉姏锛?
1. `absorb()` 璇箟涓?HDFE 澶勭悊杈圭晫
2. singleton / keepsingletons / DoF 琛屼负
3. `predict` 鎴栫粨鏋滃璞¤涔夌殑 `reghdfe` 鍛戒护绾у畬鍠?
鏈疆涓嶈姹傛妸 `reghdfe` 涓€娆″仛鎴愭渶缁堟€侊紝浣嗗繀椤昏瀹¤鏂囨。閲岀殑 鈥減lanned / missing鈥?椤规樉钁楀噺灏戙€?
## 3. 蹇呴』瀹屾垚鐨勫唴瀹?
### A. 婧愮爜鏀拺涓嬬殑缂哄彛鏀跺彛

浼樺厛鍩轰簬鏈湴婧愮爜闀滃儚锛?
- [research/vendor/stata_community/reghdfe](</D:/OneDrive - SAIF/PhD3/StataFlow/research/vendor/stata_community/reghdfe>)
- [docs/research/reghdfe-source-map.md](</D:/OneDrive - SAIF/PhD3/StataFlow/docs/research/reghdfe-source-map.md>)

鑷冲皯琛ラ綈涓嬪垪缂哄彛涓殑 **2-3 涓疄璐ㄩ」**锛?
- `keepsingletons`
- 鏇存槑纭殑 singleton dropping 璇佹嵁
- `df_a` / nested FE / absorbed DoF 鐨勬洿瀹屾暣瀹炵幇鎴栨洿绮剧‘璇箟
- `predict` 瀛愰€夐」鎵╁睍
- wrapper 灞?`absorb()` 鏇村畬鏁寸殑 Stata 椋庢牸杈撳叆澶勭悊

### B. 涓嶈兘鍙仛鈥滃弬鏁拌兘浼犺繘鍘烩€?
濡傛灉鏂板鏌愪釜鍙傛暟鎴栬涓猴紝蹇呴』鍚屾椂婊¤冻锛?
- wrapper 鍙皟鐢?- core estimator 鐪熸瀹炵幇璇ヨ涔?- support matrix 鏇存柊
- source map 鏇存柊
- 鑷冲皯涓€绫绘祴璇曡鐩栬琛屼负

绂佹鍙妸鍙傛暟鏆撮湶鍑烘潵浣嗗唴閮ㄩ潤榛樺拷鐣ャ€?
### C. 蹇呴』鏄惧紡鍖哄垎鈥滃疄鐜扳€濆拰鈥滄嫆缁濃€?
瀵逛簬鏈疆浠嶄笉鍋氱殑 `reghdfe` 鑳藉姏锛屽繀椤诲湪鏂囨。涓樉寮忓啓鍑猴細

- 鏈疄鐜?- 涓轰粈涔堟湭瀹炵幇
- 鏄惁璁″垝鍦ㄥ悗缁寘閲屽疄鐜?
涓嶅厑璁哥户缁娇鐢ㄢ€滈儴鍒嗘敮鎸佲€濅絾涓嶈鏄庡叿浣撹竟鐣岀殑鎻忚堪銆?
## 4. 娴嬭瘯瑕佹眰

### A. synthetic tests

鑷冲皯琛ヤ竴涓洿鎺ラ拡瀵规湰杞柊澧炶涓虹殑 synthetic case锛屼緥濡傦細

- singleton dropping vs keepsingletons
- nested FE DoF 鍙樺寲
- `predict` 瀛愰€夐」璇箟

### B. Stata dual-run

鑷冲皯琛?1 涓柊鐨?`reghdfe` dual-run case锛屽繀椤荤湡姝ｅ懡涓湰杞柊澧炶兘鍔涖€?
### C. full regression

瀹屾垚鍚庤嚦灏戝洖鎶ワ細

```powershell
python -m pytest tests/test_hdfe_synthetic.py -v
python -m pytest tests/golden/test_p3_reghdfe_basic.py tests/golden/test_p3_reghdfe_cluster.py tests/golden/test_p3_reghdfe_two_fe.py tests/golden/test_p3_reghdfe_real_panel.py -v
python -m pytest tests -v
```

## 5. 鏂囨。瑕佹眰

蹇呴』鍚屾鏇存柊锛?
- [docs/research/reghdfe-source-map.md](</D:/OneDrive - SAIF/PhD3/StataFlow/docs/research/reghdfe-source-map.md>)
- [docs/command-support-matrix/reghdfe.md](</D:/OneDrive - SAIF/PhD3/StataFlow/docs/command-support-matrix/reghdfe.md>)
- 濡傛湁蹇呰锛屾洿鏂?[docs/backlog.md](</D:/OneDrive - SAIF/PhD3/StataFlow/docs/backlog.md>) 鍜?[docs/testing/test-case-catalog.md](</D:/OneDrive - SAIF/PhD3/StataFlow/docs/testing/test-case-catalog.md>)

## 6. 绂佹浜嬮」

鏈疆涓嶈椤烘墜鍋氾細

- `ppmlhdfe` 鏂板姛鑳?- `ivreghdfe` 鏂板姛鑳?- DID 鍛戒护鎵╁睍
- 鏂颁竴杞€氱敤 factor grammar 鎵╁睍

闄ら潪鏌愰」宸ヤ綔鏄湰杞?`reghdfe` 鏂拌涓虹殑鐩存帴渚濊禆銆?
## 7. 瀹屾垚鏍囧噯

鏈疆閫氳繃鐨勬渶浣庢爣鍑嗭細

- `reghdfe` 鐨?support matrix 涓紝鑷冲皯涓€鎵规鍓?planned / missing 鐨勬潯鐩鐪熷疄娑堝寲
- 鏈夋柊澧炴簮鐮佹槧灏勮瘉鎹紝鑰屼笉鏄彧闈犳祴璇曡繃
- synthetic + dual-run + full regression 閮介€氳繃
- 鎶ュ憡涓槑纭啓娓呮鈥滄湰杞ˉ浜嗕粈涔堛€佽繕缂轰粈涔堚€?
濡傛灉鎶ュ憡鎶婃湰杞じ澶ф垚鈥渀reghdfe` 宸插畬鏁村鐜扳€濓紝瑙嗕负鏈畬鎴愩€?