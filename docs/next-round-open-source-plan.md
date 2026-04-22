# 涓嬩竴杞紑鍙戞€昏鍒掞細闈㈠悜寮€婧愬垵鐗堢殑鍛戒护鏄犲皠涓庢簮鐮佸畬鏁村鐜?
## 1. 鏂囨。鐩殑

鏈鍒掔敤浜庡畾涔夐」鐩湪褰撳墠 wave 鍏ㄩ儴瀹屾垚涔嬪悗鐨勪笅涓€杞€荤洰鏍囥€佸紑鍙戝師鍒欍€佽寖鍥磋竟鐣屻€佷紭鍏堢骇椤哄簭涓庨獙鏀堕棬妲涖€?
杩欎竴杞殑鐩爣涓嶆槸缁х画闆舵暎鎵╁厖灏戦噺鍔熻兘锛屼篃涓嶆槸浠呬互鈥滄祴璇曢€氳繃鈥濅负鐩爣琛ユ暟鍊硷紝鑰屾槸鎶婇」鐩粠鈥滅爺绌跺瀷 Stata 瀵归綈鍘熷瀷鈥濇帹杩涗负涓€涓彲浠ュ叕寮€鍙戝竷鐨勩€侀潰鍚戝疄璇佺爺绌惰€呯殑 Python 绗笁鏂瑰簱鍒濈増銆?
鏈疆寮€鍙戞湁涓や釜涓€绾х洰鏍囷細

1. 瀵?`research/vendor/stata_community/` 涓嬪凡闀滃儚鐨?Stata 绀惧尯寮€婧愬懡浠わ紝杩涜灏藉彲鑳藉畬鏁淬€佺郴缁熴€佹暟瀛﹀彛寰勬纭殑 Python 澶嶇幇銆?2. 灏嗗澶栨帴鍙ｆ彁鍗囦负鍛戒护绾?API锛屼娇鍑芥暟鍚嶃€佸弬鏁板懡鍚嶃€佺粨鏋滆涔夊敖閲忎笌 Stata 鍛戒护瀵归綈锛屾樉钁楅檷浣庣爺绌惰€呰縼绉绘垚鏈€?
## 2. 褰撳墠椤圭洰鐘舵€佸垽鏂?
鎴嚦鏈鍒掔紪鍐欐椂锛岄」鐩凡缁忓叿澶囦互涓嬪熀纭€锛?
- `OLS` / `FixedEffectsOLS` / `AbsorbingOLS`
- `IV2SLS` / `IVAbsorbingOLS`
- `Logit` / `Probit` / `Poisson`
- `PPMLHDFE`
- `DIDImputation` / `EventStudyInteract` / `CSDID`
- `predict` / `margins` 楂橀瀛愰泦
- synthetic + real-data 鍙岀嚎娴嬭瘯妗嗘灦
- 鏈湴 Stata runner 涓庣粨鏋?schema
- 鏈湴寮€婧愭簮鐮侀暅鍍忎笌鍏紑鏁版嵁闆嗛暅鍍?
浣嗗綋鍓嶄粛鐒跺瓨鍦ㄤ袱绫诲叧閿己鍙ｏ細

### 2.1 浜у搧灞傜己鍙?
- 瀵瑰鏆撮湶鐨勪粛涓昏鏄及璁″櫒绫伙紝鑰屼笉鏄?Stata 鍛戒护灞?API銆?- `AbsorbingOLS` 鍚屾椂鎵胯浇 `areg` 涓?`reghdfe`锛宍IVAbsorbingOLS` 鍚屾椂鎵胯浇 `ivreghdfe`锛屽懡浠よ涔夊拰瀹炵幇鍐呮牳娌℃湁鍒嗗眰銆?- `compat.stata` 鍛戒护鏄犲皠灞傚湪鏂囨。涓凡鎵胯锛屼絾浠ｇ爜涓皻涓嶅瓨鍦ㄣ€?
### 2.2 瀹屾暣搴︾己鍙?
- 瀵?`reghdfe`銆乣ivreghdfe`銆乣ppmlhdfe`銆乣did_imputation`銆乣eventstudyinteract` 绛夊懡浠わ紝鐩墠瀹炵幇鐨勬槸楂橀鏍稿績瀛愰泦锛岃€屼笉鏄畬鏁村懡浠ら潰銆?- 瀵瑰畼鏂瑰懡浠?`regress`銆乣xtreg, fe`銆乣logit`銆乣probit`銆乣poisson` 涔熶富瑕佸疄鐜颁簡褰撳墠娴嬭瘯瑕嗙洊鐨勯珮棰戣矾寰勶紝鑰屼笉鏄畬鏁?Stata 閫夐」闈€?
鍥犳锛屾湰杞紑鍙戠殑鏈川涓嶆槸鈥滃啀鍋氬嚑涓懡浠も€濓紝鑰屾槸锛?
- 鎶婂凡鏈夋暟鍊煎唴鏍告彁鍗囦负鍙紑婧愮殑鐢ㄦ埛浜у搧鎺ュ彛銆?- 鎶婂凡鏈夊瓙闆嗗疄鐜版帹杩涘埌鈥滄簮鐮佹敮鎸佷笅鐨勫畬鏁村懡浠ゅ鐜扳€濄€?
## 3. 鏈疆寮€鍙戞€诲師鍒?
鏈疆鎵€鏈夊疄鐜板繀椤婚伒瀹堜互涓嬪師鍒欍€?
### 3.1 Source-first, not test-first

瀵逛簬鏈夊叕寮€婧愮爜鐨勫懡浠わ細

- 浼樺厛鐮旂┒鏈湴闀滃儚婧愮爜銆?- 鍏堢悊瑙ｇ畻娉曘€佹暟鎹祦銆佽繑鍥炲€艰涔夈€佽嚜鐢卞害淇銆佹爣鍑嗚閫昏緫銆佽竟鐣屽鐞嗭紝鍐嶇紪鐮併€?- 涓嶅厑璁镐粎閫氳繃璋冩暣鏁板€艰繍绠楁垨瀹瑰樊鏉モ€滃榻愭祴璇曗€濄€?
瀵逛簬娌℃湁鍏紑婧愮爜鐨勫畼鏂瑰懡浠わ細

- 浠ュ畼鏂规墜鍐屻€佽繑鍥炵粨鏋溿€佸府鍔╂枃妗ｅ拰 Stata 鍙岃窇涓轰緷鎹€?- 浠嶇劧绂佹鈥滀负浜嗘祴璇曢€氳繃鑰屽弽鎺ㄦ暟鍊尖€濈殑琛屼负銆?
### 3.2 Mathematical equivalence before test equivalence

閫氳繃娴嬭瘯鍙槸鏈€浣庨棬妲涳紝涓嶆槸鏈€缁堢洰鏍囥€?
姣忎釜鍛戒护鐨?Python 瀹炵幇閮藉繀椤绘弧瓒筹細

- 鏁板瀵硅薄姝ｇ‘锛氱洰鏍?estimand 涓?Stata 鍛戒护涓€鑷淬€?- 浼拌娴佺▼姝ｇ‘锛氭牱鏈瓫閫夈€佺煩闃垫瀯閫犮€佸彉鎹€佷紭鍖栥€佹帹鏂繃绋嬩笌 Stata 閫昏緫涓€鑷淬€?- 鎺ㄦ柇璇箟姝ｇ‘锛歚t/z/chi2/F/Wald`銆佽嚜鐢卞害銆佸皬鏍锋湰淇銆乧luster 璋冩暣涓嶈兘鍙湪鏁板€间笂鈥滅宸ф帴杩戔€濄€?
濡傛灉娴嬭瘯閫氳繃浣嗘暟瀛﹁繃绋嬩笌婧愮爜鎴栨墜鍐屼笉涓€鑷达紝鍒欒涓轰笉閫氳繃銆?
### 3.3 Command-semantic API over internal-class naming

瀵瑰 API 鐨勯瑕佺洰鏍囨槸闄嶄綆 Stata 鐢ㄦ埛鐨勭悊瑙ｉ棬妲涳紝鑰屼笉鏄淮鎸佸唴閮ㄧ被鍛藉悕鐨勬暣娲佹€с€?
鍥犳鏈疆蹇呴』鎺ュ彈浠ヤ笅浜嬪疄锛?
- `areg` 鍜?`reghdfe` 鍦ㄥ唴閮ㄥ彲浠ュ叡浜唴鏍革紝浣嗗澶栧繀椤绘槸涓や釜涓嶅悓鍛戒护鍏ュ彛銆?- `ivregress 2sls` 涓?`ivreghdfe` 涔熷簲鏈夌嫭绔嬪叆鍙ｃ€?- 瀵瑰鏆撮湶鐨勫嚱鏁板悕搴斾紭鍏堜娇鐢?Stata 鍛戒护鍚嶃€?
### 3.4 No silent scope inflation

鏈疆铏界劧鐩爣鏇村ぇ锛屼絾浠嶇劧涓嶈兘鏃犺竟鐣屾墿寮犮€?
蹇呴』鍖哄垎涓夊眰鐘舵€侊細

- `implemented`: 浠ｇ爜宸插疄鐜板苟鍙皟鐢?- `verified`: 宸茬粡閫氳繃 synthetic + real-data +鏁板鍙ｅ緞瀹℃煡
- `documented-but-not-yet-complete`: 鏂囨。鐧昏浜嗕絾灏氭湭瀹屾垚

涓嶅緱鍥犱负鏌愪釜鍛戒护鈥滃凡缁忔湁绫烩€濇垨鈥滃凡鏈夊皯閲忔祴璇曗€濆氨瀵瑰瀹ｇО瀹屾暣鏀寔銆?
## 4. 鏈疆涓€绾т氦浠樼洰鏍?
鏈疆浜や粯鍒嗕负涓や釜涓诲寘銆?
### 4.1 浜や粯鍖?A锛歋tata 鍛戒护鏄犲皠灞?
鐩爣鏄湪 `src/stataflow/compat/stata/` 涓嬪缓绔嬫寮忓懡浠ゆ帴鍙ｅ眰銆?
鏈€浣庤姹傦細

- `regress(...)`
- `xtreg_fe(...)`
- `areg(...)`
- `reghdfe(...)`
- `ivregress_2sls(...)`
- `ivreghdfe(...)`
- `logit(...)`
- `probit(...)`
- `poisson(...)`
- `ppmlhdfe(...)`
- `did_imputation(...)`
- `eventstudyinteract(...)`
- `csdid(...)`

杩欎簺 wrapper 蹇呴』锛?
- 淇濇寔涓庣幇鏈夊唴鏍镐及璁″櫒瑙ｈ€?- 浣跨敤 Stata 椋庢牸鍛戒护鍚?- 鍙傛暟鍚嶅敖閲忚创杩?Stata 璇箟
- 鏄庣‘鏀寔涓庝笉鏀寔鐨勫弬鏁?- 杩斿洖缁熶竴缁撴灉瀵硅薄

### 4.2 浜や粯鍖?B锛氬紑婧愬懡浠ゅ畬鏁村鐜?
鐩爣鏄浠ヤ笅鏈湴闀滃儚鍛戒护鍋氣€滃畬鏁村害鏄捐憲鎻愬崌鈥濓細

- `reghdfe`
- `ivreghdfe`
- `ppmlhdfe`
- `did_imputation`
- `eventstudyinteract`
- `rdrobust`

鍏朵腑浼樺厛绾ф渶楂樼殑鏄墠涓変釜 HDFE 绯诲垪銆?
## 5. 鍒嗗懡浠ゅ鏌ワ細宸插疄鐜般€佹湭瀹炵幇銆佷笅涓€杞姹?
### 5.1 `regress`

褰撳墠宸插疄鐜帮細

- OLS
- `vce(ols)`
- `vce(robust)`
- `vce(cluster clustvar)`
- `aweight`
- `noconstant`
- 缂哄け鍊煎墧闄?- 鍏辩嚎鎬у墧闄?- `predict(xb residuals)`
- `margins` 楂橀瀛愰泦

褰撳墠缂哄彛锛?
- `fweight`
- `pweight`
- `iweight`
- 鏇村畬鏁寸殑 Stata 鍛戒护绾?wrapper
- 鏇村畬鏁?summary / 杈撳嚭椋庢牸灞?
鏈疆瑕佹眰锛?
- 琛?`regress()` 鍛戒护 wrapper
- 瀵规潈閲嶆敮鎸佺煩闃靛仛鏂囨。鍖?- 鏄庣‘鍝簺鏉冮噸鍦ㄥ垵鐗堝紑婧愮増鏈腑鏀寔锛屽摢浜涙爣璁颁负 planned

### 5.2 `xtreg, fe`

褰撳墠宸插疄鐜帮細

- `FixedEffectsOLS`
- `vce(ols)`
- `vce(cluster)`
- `predict(xb residuals)`
- `margins(dydx)`

褰撳墠缂哄彛锛?
- 鍛戒护绾?`xtreg_fe()` wrapper
- 鏇村畬鏁撮€夐」闈?- 鏉冮噸璺緞浠嶇己

鏈疆瑕佹眰锛?
- 琛?wrapper
- 灏嗘枃妗ｄ笌缁撴灉瀛楁鏄庣‘鏍囨垚鈥渟ingle-FE subset鈥?
### 5.3 `areg`

褰撳墠宸插疄鐜帮細

- `AbsorbingOLS(absorb=<single var>)`
- Stata 瀵归綈娴嬭瘯閫氳繃
- 鐪熷疄鏁版嵁楠岃瘉閫氳繃

褰撳墠缂哄彛锛?
- 娌℃湁姝ｅ紡 `areg()` 鍛戒护 wrapper
- 涓?`reghdfe` 鍏变韩瀹炵幇浣嗚涔夋湭鍒嗗眰
- 鍙敮鎸佸弬鏁板皻鏈樉寮忔槧灏?
鏈疆瑕佹眰锛?
- 灏?`areg` 浠?`AbsorbingOLS` 涓娊璞℃垚瀵瑰鐙珛鍛戒护鍏ュ彛
- 鏄庣‘ `areg` 鍙搴斿崟鍚告敹 FE 璇箟
- 瀵?`reghdfe` 鍏辨湁浣?`areg` 涓嶆敮鎸佺殑鍙傛暟鍋氱‖杈圭晫

### 5.4 `reghdfe`

褰撳墠宸插疄鐜帮細

- 鍩轰簬 `AbsorbingOLS` 鐨勬渶灏忓瓙闆?- `absorb()` 1-2 缁?- 鍗?cluster
- singleton drop
- 閮ㄥ垎 nested FE DoF 閫昏緫
- synthetic + real-data 瀵归綈

褰撳墠缂哄彛锛?
- 娌℃湁鐙珛 `reghdfe()` wrapper
- `vce(robust)` 灏氭湭浣滀负姝ｅ紡鍛戒护闈㈡敹鍙?- 鏈鐩栧畬鏁存簮鐮佷腑鐨勯€夐」浣撶郴
- 鏈郴缁熸瘮瀵规湰鍦伴暅鍍忎腑鐨勬祴璇曢泦鍜岃涓鸿矾寰?- 鏈舰鎴愨€滄敮鎸佺煩闃碘€?
鏈疆瑕佹眰锛?
- 寤虹珛鐙珛 `reghdfe()` 鍛戒护鍏ュ彛
- 浠ユ湰鍦伴暅鍍?[research/vendor/stata_community/reghdfe](</D:/OneDrive - SAIF/PhD3/StataFlow/research/vendor/stata_community/reghdfe>) 涓轰富鍙傝€?- 鑷冲皯瀹屾垚浠ヤ笅鍙傛暟闈細
  - `absorb()`
  - `vce(ols/robust/cluster)`
  - `cluster(varname)`
  - singleton 澶勭悊
  - 澶氱粍 FE 涓嬬殑 `df_a`
  - `predict` 楂橀瀛愰泦
- 鍚屾椂杈撳嚭涓€浠?`reghdfe` 鏀寔鐭╅樀鏂囨。锛屽垪鍑烘湭鍋氶」

### 5.5 `ivregress 2sls`

褰撳墠宸插疄鐜帮細

- `IV2SLS`
- `vce(ols/robust/cluster)`
- synthetic + real-data 瀵归綈

褰撳墠缂哄彛锛?
- 娌℃湁姝ｅ紡 `ivregress_2sls()` wrapper
- 璇婃柇宸ュ叿閾句笉瀹屾暣

鏈疆瑕佹眰锛?
- 琛?wrapper
- 鏄庣‘褰撳墠鏄惁鍙敮鎸?`2sls`
- 鎶?first-stage / weak-IV / overid 绛夌己鍙ｆ樉寮忓啓杩涙敮鎸佺煩闃?
### 5.6 `ivreghdfe`

褰撳墠宸插疄鐜帮細

- `IVAbsorbingOLS`
- FE + 2SLS + cluster 鐨勬渶灏忓瓙闆?
褰撳墠缂哄彛锛?
- 娌℃湁鐙珛 `ivreghdfe()` wrapper
- 鍜屾湰鍦伴暅鍍?[research/vendor/stata_community/ivreghdfe](</D:/OneDrive - SAIF/PhD3/StataFlow/research/vendor/stata_community/ivreghdfe>) 鐩告瘮锛屽懡浠ら潰鏄庢樉涓嶅畬鏁?
鏈疆瑕佹眰锛?
- 寤虹珛鐙珛 wrapper
- 浠ラ暅鍍忔簮鐮侀€愰」寤虹珛鍙傛暟鏀寔鐭╅樀
- 鑷冲皯鎶婃渶甯歌鍙傛暟闈㈠仛娓呮锛屽苟瀵规湭鏀寔椤圭‖鎶ラ敊

### 5.7 `logit` / `probit` / `poisson`

褰撳墠宸插疄鐜帮細

- MLE 涓昏矾寰?- `vce(ols/robust/cluster)`
- `predict`
- `margins`
- z-based inference 宸叉敹鍙?
褰撳墠缂哄彛锛?
- 鍛戒护 wrapper 灞備笉瀛樺湪
- 鏇村畬鏁寸殑 Stata 閫夐」闈笌鎶ュ憡灞備笉瀛樺湪

鏈疆瑕佹眰锛?
- 寤虹珛 `logit()` / `probit()` / `poisson()` 鍛戒护鍏ュ彛
- 鏄庣‘姣忎釜鍛戒护鐨?`predict` 涓?`margins` 鏀寔鑼冨洿
- 琛ョ粨鏋滃瓧娈典笌鏂囨。璇存槑锛岃€屼笉鏄粯璁ょ敤鎴风寽娴?
### 5.8 `ppmlhdfe`

褰撳墠宸插疄鐜帮細

- HDFE + PPML 鏈€灏忓瓙闆?- `vce(robust/cluster)`
- 鐪熷疄鏁版嵁 gravity 椋庢牸楠岃瘉

褰撳墠缂哄彛锛?
- 娌℃湁姝ｅ紡 `ppmlhdfe()` wrapper
- 涓庢湰鍦伴暅鍍?[research/vendor/stata_community/ppmlhdfe](</D:/OneDrive - SAIF/PhD3/StataFlow/research/vendor/stata_community/ppmlhdfe>) 鐩告瘮锛屼粛缂洪噸瑕佸懡浠ら潰
- `offset` / `exposure` 绛夊吀鍨嬭娉曟湭瑙佹敮鎸?- 鍒嗙闂澶勭悊灏氭湭鍋氬畬鏁磋鐩栫煩闃?
鏈疆瑕佹眰锛?
- 鐙珛 wrapper
- 浠ユ簮鐮侀暅鍍忎负涓伙紝琛ュ叏楂橀鍙傛暟
- 鎶?`offset` / `exposure` / separation 琛屼负鍒楀叆鏄庣‘寮€鍙戣寖鍥?
### 5.9 `did_imputation`

褰撳墠宸插疄鐜帮細

- 鏍稿績 estimator
- `cluster`
- `allhorizons`
- `autosample`

褰撳墠缂哄彛锛?
- 鍛戒护 wrapper 缂哄け
- 涓庡師鍛戒护甯姪鏂囨。鍜屾簮鐮佺浉姣旓紝鍙傛暟闈㈠皻涓嶅畬鏁?
鏈疆瑕佹眰锛?
- 寤虹珛 `did_imputation()` wrapper
- 鏍规嵁鏈湴婧愮爜闀滃儚琛ュ弬鏁版敮鎸佺煩闃?
### 5.10 `eventstudyinteract`

褰撳墠宸插疄鐜帮細

- 鏍稿績 estimator
- synthetic + real-data 瀵归綈

褰撳墠缂哄彛锛?
- 杈撳叆鎺ュ彛鍋忓伐绋嬪寲锛岃姹傜敤鎴烽鐢熸垚 event dummies
- 涓嶅儚 Stata 鍛戒护閭ｆ牱鍙洿鎺ヨ皟鐢?
鏈疆瑕佹眰锛?
- 寤虹珛 `eventstudyinteract()` wrapper
- 灏嗏€滈鐢熸垚铏氭嫙鍙橀噺鈥濈殑鍐呴儴瑕佹眰杞寲涓烘洿璐磋繎鍛戒护璇箟鐨勫弬鏁版帴鍙?
### 5.11 `csdid`

褰撳墠宸插疄鐜帮細

- `method="reg"` 璺緞
- `estat_event()`
- 鐪熷疄鏁版嵁鑱氬悎鏍囧噯璇凡瀵归綈

褰撳墠缂哄彛锛?
- 鍙敮鎸?`reg`
- 骞堕潪瀹屾暣 `csdid`

鏈疆瑕佹眰锛?
- 寤虹珛 `csdid()` wrapper
- 灏嗗綋鍓嶅疄鐜板畾浣嶄负 `csdid` 鐨勬渶灏忓瓙闆嗭紝鑰屼笉鏄畬鏁村懡浠?- 鏀寔鐭╅樀涓竻妤氭爣娉?`method` 闄愬埗

### 5.12 `rdrobust`

褰撳墠瀹炵幇鐘舵€侊細

- 鏈湴婧愮爜闀滃儚宸蹭笅杞?- 灏氭棤 Python 瀹炵幇

鏈疆瑕佹眰锛?
- 灏?`rdrobust` 姝ｅ紡绾冲叆寰呭疄鐜版竻鍗?- 鍏堝畬鎴愮爺绌舵。妗堝崌绾т笌鏀寔鐭╅樀璁捐
- 鏄惁杩涘叆鍒濈増寮€婧?release锛屽彇鍐充簬 HDFE 绯诲垪鏀跺彛鍚庤祫婧愭儏鍐?
## 6. API 閲嶆瀯鏂规

鏈疆蹇呴』寮曞叆鍙屽眰 API銆?
### 6.1 Core 灞備繚鐣?
鐜版湁绫荤户缁繚鐣欙紝浣滀负鍐呴儴鍜岄珮绾х敤鎴锋帴鍙ｏ細

- `OLS`
- `FixedEffectsOLS`
- `AbsorbingOLS`
- `IV2SLS`
- `IVAbsorbingOLS`
- `Logit`
- `Probit`
- `Poisson`
- `PPMLHDFE`
- `DIDImputation`
- `EventStudyInteract`
- `CSDID`

### 6.2 Compat 灞傛柊澧?
鏂板鐩綍锛?
- `src/stataflow/compat/stata/`

鏈€浣庢枃浠惰鍒掞細

- `src/stataflow/compat/stata/__init__.py`
- `src/stataflow/compat/stata/linear.py`
- `src/stataflow/compat/stata/hdfe.py`
- `src/stataflow/compat/stata/iv.py`
- `src/stataflow/compat/stata/glm.py`
- `src/stataflow/compat/stata/did.py`

瀵瑰瀵煎嚭锛?
- `regress`
- `xtreg_fe`
- `areg`
- `reghdfe`
- `ivregress_2sls`
- `ivreghdfe`
- `logit`
- `probit`
- `poisson`
- `ppmlhdfe`
- `did_imputation`
- `eventstudyinteract`
- `csdid`

### 6.3 API 璁捐鍘熷垯

- 鍛戒护鍚嶄紭鍏堜笌 Stata 瀵归綈
- 鍙傛暟鍚嶅敖閲忚创杩?Stata
- Python 渚т粛淇濈暀鍏抽敭瀛楀畨鍏ㄤ笌鍙鎬?- 涓嶆敮鎸佺殑鍙傛暟蹇呴』鏄惧紡鎶ラ敊
- 涓嶅厑璁糕€滄倓鎮勫拷鐣ュ弬鏁扳€?
## 7. 鏁板澶嶇幇涓庢簮鐮佸鐜伴棬绂?
杩欎竴杞墍鏈夌ぞ鍖哄懡浠ら兘蹇呴』澧炲姞鈥滄簮鐮佸鐜伴棬绂佲€濄€?
### 7.1 浠ｇ爜瀹炵幇鍓嶅繀椤诲畬鎴?
姣忎釜鍛戒护鍏堝舰鎴愪竴浠?`source-to-python mapping` 鏂囨。锛岃嚦灏戝寘鍚細

- 涓诲叆鍙?`.ado`
- 鏍稿績 `.mata` / 杈呭姪绋嬪簭鍏ュ彛
- 鍏抽敭缁熻瀵硅薄
- 鍏抽敭閫夐」瀵瑰摢浜涘唴閮ㄦ祦绋嬫湁褰卞搷
- Python 绔搴斿嚱鏁版垨妯″潡浣嶇疆

### 7.2 浠ｇ爜瀹℃煡鏃跺繀椤诲洖绛?
瀵规瘡涓珮椋庨櫓鍛戒护锛屽鏌ユ椂蹇呴』鑳藉洖绛旓細

- 杩欐 Python 浠ｇ爜瀵瑰簲 Stata 婧愮爜鐨勫摢涓€娈甸€昏緫
- 濡傛灉缁撴灉瀵归綈锛屾槸鍚︽槸鍥犱负閫昏緫涓€鑷达紝杩樻槸鍥犱负鏁板€间笂纰板阀鎺ヨ繎
- 鍏抽敭淇鍥犲瓙鍜岃嚜鐢卞害鍙ｅ緞鏄寜婧愮爜鎼繃鏉ョ殑锛岃繕鏄嚜琛屾帹鏂殑

濡傛灉绛斾笉鍑猴紝鍒欒涓哄鐜颁緷鎹笉瓒炽€?
### 7.3 娴嬭瘯涓嶅緱鎴愪负鍞竴鐪熷€?
绂佹涓嬪垪琛屼负锛?
- 浠呴€氳繃鏀惧瀹瑰樊璁╂祴璇曢€氳繃
- 閽堝鍗曚釜鏍蜂緥鍙嶆帹淇绯绘暟
- 閫氳繃涓存椂鏁板€煎彉鎹㈡嫙鍚堝崟娆?Stata 杈撳嚭

鍏佽鐨勫敮涓€渚嬪鏄細

- 宸茬煡鏁板€间紭鍖栧櫒宸紓瀵艰嚧鐨勬瀬灏忔诞鐐硅宸?- 涓旀暟瀛﹁矾寰勪笌婧愮爜/鎵嬪唽涓€鑷?
## 8. 鏈疆寮€鍙戦『搴?
鏈疆涓嶅缓璁钩鍧囩敤鍔涳紝搴旀寜鈥滃寮€婧愬垵鐗堜环鍊兼渶澶р€濈殑椤哄簭鎺ㄨ繘銆?
### 浼樺厛绾?A锛氬厛鍋氫骇鍝佸眰鏀跺彛

1. 寤虹珛 `compat.stata` 鍛戒护灞?2. 涓洪珮棰戝懡浠ゅ缓绔?wrapper
3. 涓烘瘡涓?wrapper 缂栧啓鏀寔鐭╅樀

杩欐槸寮€婧愬垵鐗堣兘鍚﹁鐢ㄦ埛涓婃墜鐨勯瑕佹潯浠躲€?
### 浼樺厛绾?B锛氳ˉ鍏?HDFE 绯诲垪

1. `reghdfe`
2. `ppmlhdfe`
3. `ivreghdfe`

鐞嗙敱锛?
- 杩欐槸椤圭洰鏈€鍏峰樊寮傚寲鐨勮兘鍔?- 涔熸槸鏈€鑳戒綋鐜扳€淧ython 鍙互鐪熸鏇夸唬 Stata 楂橀瀹炶瘉寤烘ā鈥濈殑閮ㄥ垎

### 浼樺厛绾?C锛氳ˉ鍏?DID 绀惧尯鍛戒护

1. `did_imputation`
2. `eventstudyinteract`
3. `csdid`

### 浼樺厛绾?D锛氬啀鑰冭檻 `rdrobust`

`rdrobust` 搴旇繘鍏ユ湰杞鍒掞紝浣嗕笉寮哄埗浣滀负鍒濈増寮€婧?release 鐨勯樆濉為」銆?
## 9. 鏂囨。涓庢不鐞嗘洿鏂拌姹?
鏈疆闄や簡浠ｇ爜瀹炵幇锛岃繕蹇呴』鍚屾鏇存柊浠ヤ笅鏂囨。锛?
- [docs/architecture/public-api.md](</D:/OneDrive - SAIF/PhD3/StataFlow/docs/architecture/public-api.md>)
- [docs/architecture/overview.md](</D:/OneDrive - SAIF/PhD3/StataFlow/docs/architecture/overview.md>)
- [docs/backlog.md](</D:/OneDrive - SAIF/PhD3/StataFlow/docs/backlog.md>)
- [docs/testing/test-case-catalog.md](</D:/OneDrive - SAIF/PhD3/StataFlow/docs/testing/test-case-catalog.md>)
- 鍚勫懡浠ょ爺绌舵。妗?
骞舵柊澧炰互涓嬫枃妗ｇ被鍨嬶細

- `docs/command-support-matrix/`
  - `reghdfe.md`
  - `ivreghdfe.md`
  - `ppmlhdfe.md`
  - `did_imputation.md`
  - `eventstudyinteract.md`
  - `csdid.md`

姣忎唤鏀寔鐭╅樀鑷冲皯鍖呮嫭锛?
- 宸叉敮鎸佸弬鏁?- 璁″垝鏀寔鍙傛暟
- 鏄庣‘涓嶆敮鎸佸弬鏁?- 褰撳墠瀵归綈璇佹嵁
- 褰撳墠宸茬煡宸紓

## 10. 鍒濈増寮€婧?release 鐨勫缓璁畾涔?
寤鸿鎶婁笅涓€杞殑鐩爣鐗堟湰瀹氫箟涓猴細

- `v0.2.0` 鎴?`v0.3.0` 寮€婧愰鍙戝竷鐗?
杩欎釜鐗堟湰鐨勬垚鍔熸爣鍑嗕笉鏄€淪tata 甯歌鍛戒护鍏ㄩ兘鍋氬畬鈥濓紝鑰屾槸锛?
1. 鐢ㄦ埛鍙互鐢?Stata 鍛戒护鍚嶈皟鐢ㄩ珮棰戝懡浠?2. `reghdfe` / `ppmlhdfe` / `ivreghdfe` 鐨勯珮棰戜富璺緞鍏峰婧愮爜鏀寔涓嬬殑鏁板澶嶇幇渚濇嵁
3. 鐮旂┒鏂囨。銆佹敮鎸佺煩闃点€佹祴璇曡瘉鎹畬鏁?4. 鏈敮鎸佸姛鑳借娓呮櫚鏍囪瘑锛岃€屼笉鏄ā绯婂鐞?
## 11. 鏈疆涓嶅缓璁珛鍒绘壙璇虹殑鍐呭

涓轰簡閬垮厤鑼冨洿澶辨帶锛屾湰杞笉寤鸿鎶婁互涓嬪唴瀹逛綔涓哄垵鐗?release 鐨勭‖闃诲锛?
- 瀹屾暣 `rdrobust`
- multi-way cluster 鐨勫叏鍛戒护缁熶竴瀹炵幇
- 瀹屾暣 `margins`
- 鎵€鏈夊懡浠ょ殑瀹屾暣 `predict` 瀛愰€夐」
- 鎵€鏈夊畼鏂瑰懡浠ょ殑鍏ㄩ儴鏉冮噸璇硶
- 鎵€鏈?DID 鍛戒护鐨勫畬鏁撮€夐」闈?
杩欎簺閮藉彲浠ヨ繘鍏ュ悗缁増鏈紝浣嗕笉搴旀姠鍗?HDFE 鍛戒护闈笌 API 鏀跺彛鐨勪紭鍏堢骇銆?
## 12. 涓嬩竴姝ユ墽琛屽缓璁?
鏈鍒掕惤鍦板悗锛屽悗缁墽琛屽簲鍒嗕负涓夌被浠诲姟锛?
1. `API restructuring tasks`
   - 寤虹珛 `compat.stata`
   - 琛?wrapper
   - 閲嶅啓鍏紑鍏ュ彛涓?README 绀轰緥

2. `source-backed completion tasks`
   - 閫愪釜鍛戒护瀵圭収鏈湴闀滃儚婧愮爜琛ュ叏鍔熻兘
   - 浼樺厛 `reghdfe` / `ppmlhdfe` / `ivreghdfe`

3. `support-matrix and release-hardening tasks`
   - 杈撳嚭鏀寔鐭╅樀
   - 娓呯悊鍛戒护杈圭晫
   - 涓哄紑婧愬垵鐗堝仛鏂囨。涓庡懡鍚嶆敹鍙?
鏈鍒掓槸涓嬩竴杞紑鍙戠殑鎬荤翰锛屼笉鐩存帴鏇夸唬浠诲姟鍗°€傚悗缁墍鏈?Claude Code 鎵ц浠诲姟閮藉簲浠庢湰璁″垝缁х画鎷嗚В锛岃€屼笉鏄噸鏂板畾涔夋柟鍚戙€?