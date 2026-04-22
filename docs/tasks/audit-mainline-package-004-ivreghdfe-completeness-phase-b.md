# 瀹¤涓荤嚎浠诲姟鍖?004锛歚ivreghdfe` 瀹屾暣搴︽帹杩涳紙Phase B锛?
## 浠诲姟瀹氫綅

鏈疆杩涘叆瀹¤涓荤嚎鐨勪笅涓€鏉″懡浠ゆ棌锛歚ivreghdfe`銆?
鐩爣涓嶆槸鍐嶅仛涓€涓€滆兘璺戠殑 2SLS + FE 瀛愰泦鈥濓紝鑰屾槸鎶婂綋鍓嶅疄鐜颁粠楂橀瀛愰泦鎺ㄨ繘鍒版洿鎺ヨ繎 `ivreghdfe` 鍛戒护鏈韩鐨勫畬鏁磋涔夛紝骞朵笖浠ユ湰鍦?vendor 婧愮爜涓虹害鏉燂紝鑰屼笉鏄崟绾洿缁曟祴璇曟暟鍊艰皟鍙傘€?
## 鐩爣

鏈疆鑷冲皯瀹屾垚涓嬮潰涓夌被宸ヤ綔涓殑鍓嶄袱绫伙紝骞跺敖閲忔帹杩涚涓夌被锛?
1. **鍛戒护闈㈣ˉ榻?*
   - 澶嶆牳骞惰ˉ榻愬綋鍓?wrapper / core 宸茬己澶变絾灞炰簬楂橀 `ivreghdfe` 浣跨敤闈㈢殑鍙傛暟鎴栬涓恒€?2. **source-backed 鏀跺彛**
   - 鎶?`docs/research/ivreghdfe-source-map.md` 鏇存柊鎴愮湡姝ｅ彲浣滀负瀹¤渚濇嵁鐨勬槧灏勬枃妗ｃ€?3. **璇佹嵁閾捐ˉ寮?*
   - 涓烘湰杞柊澧炴垨绾犳鐨勮兘鍔涜ˉ synthetic / real-data / source-backed 璇佹嵁锛岃€屼笉鏄彧琛?wrapper delegation 娴嬭瘯銆?
## 蹇呴』浣跨敤鐨勪緷鎹?
- 鏈湴婧愮爜闀滃儚锛?  - `research/vendor/stata_community/ivreghdfe/`
- 鐜版湁鐮旂┒鏂囨。锛?  - `docs/research/ivreghdfe-source-map.md`
- 褰撳墠鏀寔鐭╅樀锛?  - `docs/command-support-matrix/ivreghdfe.md`

## 蹇呴』閲嶇偣瀹¤鐨勫唴瀹?
### A. 鍛戒护璇箟涓庡弬鏁伴潰

鑷冲皯妫€鏌ュ苟鏄庣‘涓嬪垪椤圭洰褰撳墠鐘舵€侊細

- `absorb()`
- `vce(ols|robust|cluster)`
- `cluster()`
- `noconstant`
- `keepsingletons`
- `first-stage` / first-stage evidence 鏄惁缂哄け
- `predict()` 璇箟鏄惁瀹屾暣
- wrapper 鏄惁鐪熺殑鐢?Stata 鍛戒护鍚嶄笖鍏叡璇箟姝ｇ‘

### B. 浼拌涓庢帹鏂繃绋?
鑷冲皯瀹¤骞惰鏄庯細

- FE 娈嬪樊鍖栦笌 IV 涓ら樁娈垫槸濡備綍缁勫悎鐨?- robust / cluster VCE 鍦?`ivreghdfe` 涓槸鍚︿笌鏈湴婧愮爜閫昏緫鍙槧灏?- DoF / `df_a` / `df_model` / `df_resid` 鍙ｅ緞鏄惁鍜屽綋鍓?`reghdfe` / `ivregress 2sls` 浣撶郴涓€鑷?
### C. 缁撴灉瀵硅薄涓?postestimation

鑷冲皯鏄庣‘锛?
- 褰撳墠 `ResultSchema` 閲屽摢浜涘瓧娈靛凡缁忔湁 `ivreghdfe` 璇箟
- 鏄惁鏀寔 `predict(type="xb")`
- 鏄惁闇€瑕佹槑纭嫆缁濆皻鏈敮鎸佺殑 predict 瀛愰€夐」

## 鏈€浣庝氦浠樿姹?
### 1. 浠ｇ爜灞?
濡傜‘鏈夊繀瑕侊紝鍙互淇敼锛?
- `src/stataflow/estimators/iv.py`
- `src/stataflow/compat/stata/iv.py`
- 浠ュ強鐩存帴鐩稿叧鐨勭粨鏋?/ 宸ュ叿灞傛枃浠?
浣嗙姝細

- 椤烘墜鏀逛笌 `ivreghdfe` 鏃犲叧鐨?factor grammar
- 椤烘墜鎵?`reghdfe`銆乣ppmlhdfe`銆丏ID 鍛戒护

### 2. 鏂囨。灞?
蹇呴』鏇存柊锛?
- `docs/research/ivreghdfe-source-map.md`
- `docs/command-support-matrix/ivreghdfe.md`

濡傛湰杞柊澧炴祴璇曟牱渚嬶紝涔熷繀椤诲悓姝ワ細

- `docs/testing/test-case-catalog.md`
- `docs/backlog.md`锛堣嫢瀹屾暣搴︾姸鎬佸彂鐢熷彉鍖栵級

### 3. 娴嬭瘯灞?
蹇呴』鑷冲皯琛ユ垨澶嶆牳浠ヤ笅璇佹嵁锛?
- synthetic:
  - `ivreghdfe` 鍩虹
  - `ivreghdfe` robust
  - `ivreghdfe` cluster
  - 濡傛湰杞柊澧?`predict`锛岄渶瑕佸搴?synthetic 琛屼负娴嬭瘯
- real-data:
  - 鑷冲皯淇濇寔鐜版湁 real panel dual-run 閫氳繃
- source-backed:
  - 鍦?`REPORT.md` 涓鏄庢湰杞柊澧炶兘鍔涗笌 vendor 婧愮爜鍝竴娈电浉瀵瑰簲

## 鏄庣‘绂佹

- 涓嶅厑璁稿彧闈犳斁瀹藉宸 dual-run 杩囧叧
- 涓嶅厑璁稿彧琛?wrapper delegation 娴嬭瘯灏卞绉板懡浠ゅ畬鏁村害鎻愬崌
- 涓嶅厑璁稿湪娌℃湁婧愮爜/鎵嬪唽渚濇嵁鏃讹紝涓轰簡鍜岀幇鏈夋牱渚嬫暟鍊间竴鑷村幓纭皟瀹炵幇
- 涓嶅厑璁告妸鈥滃凡鏀寔楂橀瀛愰泦鈥濆啓鎴愨€滃凡瀹屾暣瀹炵幇 `ivreghdfe`鈥?
## 閫氳繃鏍囧噯

Codex 鍙細鍦ㄤ互涓嬫潯浠跺悓鏃舵弧瓒虫椂鏀捐锛?
1. `ivreghdfe` 鐨勬湰杞洰鏍囪兘鍔涙湁瀹為檯浠ｇ爜鎴栨槑纭殑鍏叡鎺ュ彛鏀跺彛锛屼笉鍙槸鏂囨。淇敼銆?2. `docs/research/ivreghdfe-source-map.md` 涓庡綋鍓嶄唬鐮佷竴鑷达紝涓嶄繚鐣欒繃鏈熺粨璁恒€?3. `docs/command-support-matrix/ivreghdfe.md` 涓?wrapper / estimator / 娴嬭瘯涓€鑷淬€?4. 鏈夎嚦灏戜竴椤规柊澧炵殑 source-backed 璇佹嵁锛岃€屼笉鏄粎澶嶇敤鏃ф祴璇曘€?5. 閲嶆柊璺戠浉鍏充笓椤规祴璇曞拰鍏ㄩ噺娴嬭瘯閫氳繃銆?
## 鍥炴姤鏍煎紡

瀹屾垚鍚庡湪 `workspace/current-task/REPORT.md` 涓寜涓嬮潰缁撴瀯姹囨姤锛?
1. 鏈疆鏂板鎴栦慨姝ｄ簡鍝簺 `ivreghdfe` 鑳藉姏
2. 姣忛」鑳藉姏瀵瑰簲鍝鏈湴婧愮爜渚濇嵁
3. 鍝簺浠嶇劧缂哄け锛屼负浠€涔堢己澶?4. 鏂板浜嗗摢浜涙祴璇曚笌璇佹嵁
5. fresh run 缁撴灉
6. 浣犺涓烘湰杞悗 `ivreghdfe` 鐨勫畬鏁村害璇勭骇锛歚partial / near-complete / full`锛屽苟缁欏嚭鐞嗙敱
