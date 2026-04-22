# 瀹¤涓荤嚎浠诲姟鍖?005锛欴ID 绀惧尯鍛戒护瀹屾暣搴︽帹杩涳紙Phase B锛?## 浠诲姟瀹氫綅

`reghdfe`銆乣ppmlhdfe`銆乣ivreghdfe` 涓荤嚎宸茬粡鎺ㄨ繘鍒板彲楠岃瘉鐨?Phase B 瀛愰泦銆備笅涓€鏉′富绾胯繘鍏?DID 绀惧尯鍛戒护鏃忥細

- `did_imputation`
- `eventstudyinteract`
- `csdid`

鏈疆鐩爣涓嶆槸鈥滃啀琛ュ嚑涓?wrapper 娴嬭瘯鈥濓紝鑰屾槸鎶婅繖涓変釜鍛戒护浠庘€滈珮棰戞牳蹇冭矾寰勫彲璺戔€濇帹杩涘埌鈥滃懡浠よ涔夈€佹簮鐮佷緷鎹€佺湡瀹炴暟鎹瘉鎹€佸叕寮€鏀寔鐭╅樀鏇存帴杩戝彲鍙戝竷鐘舵€佲€濈殑 Phase B銆?
## 鐩爣

鏈疆鑷冲皯瀹屾垚涓嬮潰鍥涚被宸ヤ綔涓殑鍓嶄笁绫伙細

1. **鍛戒护闈㈣ˉ榻?*
   - 澶嶆牳骞惰ˉ榻愬綋鍓?wrapper / core 宸茬己澶变絾灞炰簬楂橀 DID 浣跨敤闈㈢殑鍙傛暟銆佽竟鐣屼笌閿欒璇箟銆?2. **source-backed 鏀跺彛**
   - 鎶?`did_imputation`銆乣eventstudyinteract` 鐨?source map 鏀跺彛鎴愮湡姝ｅ彲瀹¤鏂囨。銆?   - 鏄庣‘ `csdid` 鐨勫綋鍓嶈竟鐣岋紝涓嶅厑璁哥户缁ā绯婃弿杩般€?3. **鐪熷疄鏁版嵁涓庢暟瀛﹁瘉鎹寮?*
   - 涓嶆槸鍙噸澶嶆棫鏍蜂緥锛岃€屾槸琛ユ洿鏈夎鏈嶅姏鐨?real-data / edge-case 璇佹嵁銆?4. **鏀寔鐭╅樀涓?README 瀵归綈**
   - 璁?DID 鍛戒护鐨?support matrix 涓?wrapper銆乧ore estimator銆佹祴璇曠姸鎬佸畬鍏ㄤ竴鑷淬€?
## 蹇呴』浣跨敤鐨勪緷鎹?
- 鏈湴婧愮爜闀滃儚锛?  - `research/vendor/stata_community/did_imputation/`
  - `research/vendor/stata_community/eventstudyinteract/`
- 鐜版湁鐮旂┒鏂囨。锛?  - `docs/research/did_imputation.md`
  - `docs/research/eventstudyinteract.md`
  - `docs/research/csdid.md`
- 鐜版湁娴嬭瘯涓庡叕寮€鏁版嵁锛?  - `tests/golden/test_w4_*`
  - `research/data/public/`
- 瀹℃煡鍗忚锛?  - `docs/operations/codex-review-protocol.md`

## 蹇呴』閲嶇偣瀹¤鐨勫唴瀹?
### A. 鍛戒护璇箟涓庡弬鏁伴潰

鑷冲皯妫€鏌ュ苟鏄庣‘褰撳墠浠ヤ笅鍐呭鐨勭姸鎬侊細

- `did_imputation`
  - `allhorizons`
  - `autosample`
  - `window`
  - `pretrend`
  - `minn`
- `eventstudyinteract`
  - 鑷姩 event-dummy 鐢熸垚
  - cohort / control group 璇箟
  - cluster 璇箟
- `csdid`
  - 褰撳墠鍙敮鎸?`method="reg"` 鐨勮竟鐣?  - `estat_event()` 杈撳嚭鍙ｅ緞
  - 瀵规湭鏀寔 method 鐨勬樉寮忔嫆缁?
### B. 鏁板杩囩▼涓庢帹鏂?
鑷冲皯璇存槑锛?
- 鍚勫懡浠ょ殑浼拌鐩爣涓庤仛鍚堣繃绋嬫槸鍚﹁兘鐢辨簮鐮佹垨鎵嬪唽鏀寔
- 鏍囧噯璇€佽仛鍚堟爣鍑嗚銆佷簨浠舵椂闂寸郴鏁扮殑鐢熸垚涓庡綋鍓嶅疄鐜板浣曞搴?- 鏄惁瀛樺湪鈥滈€氳繃瀹藉宸€濇帺鐩栧疄鐜板樊寮傜殑鏃ч棶棰橈紱鑻ュ瓨鍦紝蹇呴』淇帀锛屼笉鍏佽缁х画鐣欏湪鏈疆

### C. 缁撴灉瀵硅薄涓庡叕寮€鎺ュ彛

鑷冲皯璇存槑锛?
- wrapper 杩斿洖瀵硅薄鍜?core estimator 鐨勮亴璐ｈ竟鐣?- 鍝簺 postestimation 璇箟宸茬粡鏀寔锛屽摢浜涙病鏈?- 鏂囨。涓嶈兘鎶娾€渃ore 鏀寔鈥濊鍐欐垚鈥渨rapper 鏀寔鈥?
## 鏈€浣庝氦浠樿姹?
### 1. 浠ｇ爜灞?
濡傜‘鏈夊繀瑕侊紝鍙互淇敼锛?
- `src/stataflow/estimators/did_imputation.py`
- `src/stataflow/estimators/eventstudyinteract.py`
- `src/stataflow/estimators/csdid.py`
- `src/stataflow/compat/stata/did.py`
- 涓庝笂杩扮洿鎺ョ浉鍏崇殑缁撴灉鎴栧伐鍏峰眰鏂囦欢

浣嗙姝細

- 椤烘墜鏀逛笌 DID 涓荤嚎鏃犲叧鐨?factor grammar
- 椤烘墜淇敼 HDFE / IV / GLM 涓荤嚎浠ｇ爜

### 2. 鏂囨。灞?
蹇呴』鏇存柊锛?
- `docs/research/did_imputation-source-map.md`
- `docs/research/eventstudyinteract-source-map.md`
- `docs/command-support-matrix/did_imputation.md`
- `docs/command-support-matrix/eventstudyinteract.md`
- `docs/command-support-matrix/csdid.md`

濡傛湰杞柊澧為暱鏍蜂緥锛屼篃蹇呴』鍚屾锛?
- `docs/testing/test-case-catalog.md`
- `docs/backlog.md`锛堣嫢瀹屾暣搴︾姸鎬佸彂鐢熷彉鍖栵級

### 3. 娴嬭瘯灞?
蹇呴』鑷冲皯琛ユ垨澶嶆牳浠ヤ笅璇佹嵁锛?
- synthetic:
  - 涓変釜 DID 鍛戒护鑷冲皯鍚勬湁涓€椤归潪骞冲嚒 synthetic 鎴?edge-case 琛屼负娴嬭瘯
- real-data:
  - 淇濇寔鐜版湁 `ezunem` 绛夌湡瀹炴暟鎹?dual-run 閫氳繃
  - 鑷冲皯鏂板涓€绫绘洿鐏垫椿鐨?real-data 鎴?edge-case 楠岃瘉
- source-backed:
  - 鍦?`REPORT.md` 閲屾槑纭鏄庢瘡涓懡浠ゆ湰杞柊澧炶兘鍔涘搴斿摢娈垫湰鍦版簮鐮佹垨鍝潯鎵嬪唽渚濇嵁

## 鏄庣‘绂佹

- 涓嶅厑璁稿彧闈犳斁瀹?real-data 瀹瑰樊灏卞绉?DID 鍛戒护瀹屾暣搴︽彁鍗?- 涓嶅厑璁稿彧鍋?wrapper delegation 娴嬭瘯灏辫鈥滃懡浠ゆ洿瀹屾暣鈥?- 涓嶅厑璁告妸 `csdid(method=\"reg\")` 鐨勫崟涓€璺緞鍐欐垚鈥滃凡瀹屾暣瀹炵幇 csdid鈥?- 涓嶅厑璁稿湪娌℃湁婧愮爜/鎵嬪唽渚濇嵁鏃朵负浜嗛€氳繃娴嬭瘯鍘昏皟鏁板€?
## 閫氳繃鏍囧噯

Codex 鍙細鍦ㄤ互涓嬫潯浠跺悓鏃舵弧瓒虫椂鏀捐锛?
1. 涓変釜 DID 鍛戒护涓紝鏈疆鐩爣鑳藉姏鏈夊疄闄呬唬鐮併€佹帴鍙ｆ垨鏄惧紡杈圭晫鏀跺彛锛岃€屼笉鏄彧鏀规枃妗ｃ€?2. `did_imputation-source-map.md`銆乣eventstudyinteract-source-map.md` 涓庡綋鍓嶅疄鐜颁竴鑷淬€?3. `csdid` 鐨勬敮鎸佺煩闃典笌 wrapper / estimator / 娴嬭瘯涓€鑷达紝杈圭晫璇存硶娓呮銆?4. 鏈夎嚦灏戜竴椤规柊澧炵殑 source-backed 璇佹嵁锛岃€屼笉鏄彧澶嶇敤鏃?Wave 4 缁撴灉銆?5. 鐩稿叧涓撻」娴嬭瘯鍜屽叏閲忔祴璇曢€氳繃銆?
## 宸茬煡寤跺悗椤癸紙涓嶉樆濉炴湰杞級

- `ivreghdfe` Phase B 鐨?`REPORT.md` fresh-run 璇佹嵁浠嶆湁鏃ф暟瀛楁畫鐣欍€?- 璇ラ棶棰樺凡鐧昏鍦細
  - `workspace/current-task/review-audit-mainline-package-004-final-codex.md`
  - `docs/tasks/audit-mainline-package-004-rework-report-evidence.md`
- 鏈疆涓嶈姹傚鐞嗚闂锛屼篃涓嶈椤烘墜鍐嶆敼 `ivreghdfe` 涓荤嚎銆?
## 鍥炴姤鏍煎紡

瀹屾垚鍚庡湪 `workspace/current-task/REPORT.md` 涓寜涓嬮潰缁撴瀯姹囨姤锛?
1. 鏈疆鏂板鎴栦慨姝ｄ簡鍝簺 DID 鍛戒护鑳藉姏
2. 姣忛」鑳藉姏瀵瑰簲鍝簺婧愮爜鎴栨墜鍐屼緷鎹?3. 鍝簺浠嶇劧缂哄け锛屼负浠€涔堢己澶?4. 鏂板浜嗗摢浜?synthetic / real-data / source-backed 璇佹嵁
5. fresh run 缁撴灉
6. 浣犺涓?`did_imputation`銆乣eventstudyinteract`銆乣csdid` 鍚勮嚜褰撳墠搴旇瘎涓?`partial / near-complete / full`锛屽苟缁欏嚭鐞嗙敱
