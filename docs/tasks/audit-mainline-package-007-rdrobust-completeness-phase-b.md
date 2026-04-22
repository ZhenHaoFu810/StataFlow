# 瀹¤涓荤嚎浠诲姟鍖?007锛歚rdrobust` 瀹屾暣搴︽帹杩涳紙Phase B锛?
## 浠诲姟瀹氫綅

`rdrobust` 鐩墠宸茬粡浠?鈥渕issing鈥?鎺ㄨ繘鍒?**鍙獙璇佺殑鏈€灏?sharp RD 瀛愰泦**锛屼絾璺濈甯歌鐮旂┒宸ヤ綔娴佷粛鏈夋槑鏄剧己鍙ｃ€?
褰撳墠鏀寔鐭╅樀鎶?`rdrobust` 瀹氫负 **Partial / Minimal Subset**锛屾渶澶х殑鍙敤鎬х己鍙ｆ槸锛?
- 蹇呴』鏄惧紡鎻愪緵 `h`锛屼笉鑳借嚜鍔ㄥ甫瀹介€夋嫨
- 涓嶆敮鎸?`covs()`
- 涓嶆敮鎸佹洿瀹屾暣鐨勭粨鏋滀笌鍛戒护灞傝涔?
涓嬩竴姝ヤ笉鍐嶆í鍚戞墿鍏朵粬鍛戒护锛岃€屾槸鎶?`rdrobust` 浠庘€滄渶灏忓彲璺戔€濇帹杩涘埌鈥滃父瑙?sharp RD 宸ヤ綔娴佸彲鐢ㄢ€濈殑 **Phase B 瀛愰泦**銆?
## 鐩爣

鏈疆鑷冲皯瀹屾垚涓嬮潰涓夌被宸ヤ綔涓殑鍓嶄袱绫伙紝鏈€濂戒笁绫诲叏閮ㄥ畬鎴愶細

1. **鑷姩甯﹀閫夋嫨杩涘叆涓荤嚎**
   - 鏀寔鑷冲皯涓€涓父瑙?selector锛屽苟缁欏嚭娓呮櫚鐨?source-backed 瀵瑰簲鍏崇郴銆?2. **covariate-adjusted sharp RD 杩涘叆涓荤嚎**
   - 鏀寔 `covs()` 鐨勬渶灏忎絾姝ｇ‘瀛愰泦銆?3. **`rdrobust` 瀵瑰鏂囨。涓庨獙璇佽瘉鎹敹鍙?*
   - source map銆乻upport matrix銆丷EADME / release-facing 鏂囨。鍚屾鏇存柊銆?
## 蹇呴』浣跨敤鐨勪緷鎹?
- 瀹¤鏂囨。锛?  - `docs/audit/audit-findings.md`
  - `docs/audit/project-gaps.md`
  - `docs/audit/next-development-plan.md`
- 鐮旂┒妗ｆ锛?  - `docs/research/rdrobust-source-map.md`
- 鏈湴婧愮爜闀滃儚锛?  - `research/vendor/stata_community/rdrobust/`
- 褰撳墠鏀寔鐭╅樀锛?  - `docs/command-support-matrix/rdrobust.md`
- 瀹℃煡鍗忚锛?  - `docs/operations/codex-review-protocol.md`

## 鏁板涓庡疄鐜拌姹?
### A. 涓ョ鈥滀负杩囨祴璇曞弽鎺ㄦ暟鍊尖€?
鏈疆蹇呴』鍧氭寔浠ヤ笅瑙勫垯锛?
- 鍏堟槑纭?Stata / 瀹樻柟 Python / 璁烘枃鍏紡鐨勫搴斿叧绯伙紝鍐嶅啓瀹炵幇
- 涓嶅厑璁搁€氳繃鏀惧瀹瑰樊銆佺壒娈?case 淇ˉ銆佸鍗曚竴鏍蜂緥璋冨弬鏉ュ绉板畬鎴?- 鑷姩甯﹀涓?covariate-adjusted RD 鐨勫疄鐜板繀椤昏兘瑙ｉ噴娓呮浼拌娴佺▼銆佸亸宸慨姝ｅ拰 VCE 鍙ｅ緞

### B. 鑷姩甯﹀閫夋嫨

鑷冲皯鏀寔 **涓€涓?* 楂橀 selector锛屽苟鏄庣‘鍐欐竻妤氾細

- 閫変腑鐨?selector 鏄粈涔?- 涓?Stata `rdrobust` / `rdbwselect` 鐨勫摢涓垎鏀搴?- 褰撳墠鏄惁鍙敮鎸?sharp RD / local linear / 鏌愪簺 kernel 缁勫悎

浼樺厛寤鸿锛?
- `bwselect="mserd"` 鎴栫瓑浠风殑鏈€甯歌 sharp RD selector

鏈疆涓嶈姹備竴娆℃€ц鐩栧叏閮?selector 瀹舵棌锛屼絾蹇呴』锛?
- wrapper 鑳芥帴鍙?`bwselect=...`
- 鑻ユ湭鏀寔鍏朵粬 selector锛屽繀椤绘樉寮?hard-reject
- 鑻?`h` 涓?`bwselect` 鍚屾椂缁欏嚭锛岃涓哄繀椤绘槑纭笖鏂囨。鍖?
### C. `covs()` 鏈€灏忓瓙闆?
鏈疆鑻ュ疄鐜?`covs()`锛屽繀椤绘弧瓒筹細

- 浠呭湪 sharp RD 涓嬪厛鏀寔
- 鏄庣‘鏍锋湰绛涢€夊拰缂哄け鍊煎鐞?- 鏄庣‘ covariate-adjusted local polynomial 鐨勪及璁″彛寰?- 瀵逛笉鏀寔鐨勬墿灞曞満鏅紙濡?fuzzy + covs銆乧luster + covs锛夋樉寮?hard-reject

### D. 缁撴灉瀵硅薄涓庡懡浠よ涔?
鑻ユ柊澧炶嚜鍔ㄥ甫瀹芥垨 covariates锛岃嚦灏戣淇濊瘉锛?
- 缁撴灉瀵硅薄涓富甯﹀銆佸亸宸甫瀹藉拰鏈夋晥鏍锋湰浠嶇劧鍙
- wrapper 鍛戒护灞傚弬鏁颁笌 Stata 鍛戒护璇箟涓€鑷?- 涓嶅厑璁稿嚭鐜?README / support matrix 鍐欐敮鎸併€佷絾 wrapper 瀹為檯涓嶆帴鍙楃殑鎯呭喌

## 蹇呴』閲嶇偣瀹¤鐨勫唴瀹?
### 1. 婧愮爜鏄犲皠

蹇呴』鎶婁互涓嬮€昏緫鍐欒繘 `docs/research/rdrobust-source-map.md`锛?
- 鑷姩甯﹀閫夋嫨瀵瑰簲鐨勬簮鐮佸叆鍙ｄ笌 Python 鏄犲皠
- `covs()` 瀵瑰簲鐨勬簮鐮?/ 鍏紡鍒嗘敮涓?Python 鏄犲皠
- 褰撳墠浠嶆湭瀹炵幇鐨勫弬鏁伴潰

### 2. 鏀寔鐭╅樀

蹇呴』鏇存柊 `docs/command-support-matrix/rdrobust.md`锛?
- `Supported Parameters`
- `Planned Parameters`
- `Explicitly Unsupported Parameters`
- `Alignment Evidence`

涓嶅厑璁稿啀鎶婂凡瀹炵幇鍙傛暟鏀惧湪 planned锛屼篃涓嶅厑璁告妸鏈疄鐜板弬鏁板啓寰楁ā绯娿€?
### 3. 娴嬭瘯璁捐

鏈疆娴嬭瘯涓嶈兘鍙仛鈥滄暟鍊煎涓€涓嬧€濄€?
鑷冲皯瑕佸寘鍚細

- synthetic锛?  - 鑷姩甯﹀ selector 琛屼负
  - covariate-adjusted sharp RD
  - `h` / `bwselect` 鍐茬獊鎴栦紭鍏堢骇璇箟
- real-data锛?  - 鑷冲皯涓€涓叕寮€ RD 鏁版嵁涓婄殑 dual-run锛堢户缁彲鐢?`rdrobust_senate.dta`锛屽闇€瑕佸彲琛ユ柊鏁版嵁锛?- negative tests锛?  - 涓嶆敮鎸佺殑鍙傛暟蹇呴』鏄惧紡鎶ラ敊锛屼笉鑳介潤榛樺拷鐣?
### 4. wrapper / example / 鏂囨。涓€鑷存€?
鑻?README 鎴?support matrix 瀹ｇО `bwselect` / `covs` 鍙敤锛屽垯锛?
- wrapper 蹇呴』鐪熺殑鎺ュ彈
- 鑷冲皯涓€涓?example 鎴?smoke 璇佹嵁蹇呴』鑳借窇

## 鏈€浣庝氦浠樿姹?
### 1. 浠ｇ爜灞?
鍏佽淇敼锛?
- `src/stataflow/estimators/rdrobust.py`
- `src/stataflow/compat/stata/rd.py` 鎴栧搴?wrapper 鏂囦欢
- 蹇呰鐨勭粨鏋?schema / helper

### 2. 鏂囨。灞?
蹇呴』鏇存柊锛?
- `docs/research/rdrobust-source-map.md`
- `docs/command-support-matrix/rdrobust.md`

濡傜‘鏈夊繀瑕侊紝鍙悓姝ユ洿鏂帮細

- `README.md`
- `docs/release/open-source-alpha-status.md`
- `docs/release/known-issues.md`

### 3. 娴嬭瘯灞?
鑷冲皯蹇呴』鏂板鎴栨洿鏂帮細

- `tests/test_rdrobust.py`
- 蹇呰鐨?golden / dual-run 娴嬭瘯
- 鑻ユ柊澧?example锛屽垯琛?smoke 璇佹嵁

## 鏄庣‘绂佹

- 涓嶉『鎵嬫敼 `reghdfe` / `ppmlhdfe` / `ivreghdfe` / DID 鍐呮牳
- 涓嶆妸 fuzzy RD銆乧luster RD銆佸叏閮?selector 瀹舵棌涓€鍙ｆ皵濉炶繘鏈疆鍚庡啀鐢ㄥぇ瀹瑰樊鏀捐
- 涓嶅厑璁稿 unsupported 鍙傛暟闈欓粯蹇界暐
- 涓嶅厑璁稿彧渚濇嵁瀹樻柟 Python 鍖呰緭鍑鸿€屼笉瑙ｉ噴 Stata / 璁烘枃 / 婧愮爜瀵瑰簲鍏崇郴

## 閫氳繃鏍囧噯

Codex 鍙細鍦ㄤ互涓嬫潯浠跺悓鏃舵弧瓒虫椂鏀捐锛?
1. 鑷冲皯涓€涓嚜鍔ㄥ甫瀹?selector 杩涘叆鍛戒护灞傦紝涓?source-backed 璇存槑娓呮銆?2. 鑻ュ疄鐜?`covs()`锛屽叾浼拌鍙ｅ緞銆乂CE 鍙ｅ緞鍜岀己澶卞€煎鐞嗘湁鏄庣‘渚濇嵁銆?3. `rdrobust` source map銆乻upport matrix銆亀rapper銆佹祴璇曡瘉鎹竴鑷淬€?4. 鍏ㄩ噺娴嬭瘯閫氳繃锛屽苟涓?`rdrobust` 涓撻」娴嬭瘯 / dual-run 閫氳繃銆?5. 涓嶆敮鎸佺殑鍙傛暟浠嶇劧琚樉寮?hard-reject銆?
## 鍥炴姤鏍煎紡

瀹屾垚鍚庡湪 `workspace/current-task/REPORT.md` 涓寜涓嬮潰缁撴瀯姹囨姤锛?
1. 鑷姩甯﹀閫夋嫨瀹炵幇浜嗕粈涔堛€佹病鏈夊疄鐜颁粈涔?2. `covs()` 瀹炵幇浜嗕粈涔堛€佹病鏈夊疄鐜颁粈涔?3. 浼拌杩囩▼ / 鍋忓樊淇 / VCE 鏄浣曚笌 Stata 鎴栧畼鏂规簮鐮佸搴旂殑
4. 鏇存柊浜嗗摢浜?source map / support matrix / release-facing 鏂囨。
5. 璺戜簡鍝簺 synthetic / dual-run / full pytest
6. 鏈€鏂?fresh run 缁撴灉
7. 褰撳墠 `rdrobust` 璺濈鈥滃畬鏁?community command 澶嶇幇鈥濊繕宸粈涔?