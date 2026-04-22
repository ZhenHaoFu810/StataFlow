# Validation Package 001: Out-of-Sample Public Evidence Book

## Task Positioning

鏈疆浠诲姟鏄竴娆?**瀹屾暣銆佷竴娆℃€т笅鍙戠殑 out-of-sample validation 浠诲姟鍖?*銆? 
鐩爣涓嶆槸缁х画鎵╁姛鑳斤紝鑰屾槸绯荤粺璇佹槑锛?
> 褰撳墠 `stataflow` 宸插疄鐜板懡浠わ紝鍦?**鏂扮殑鍏紑鐪熷疄鏁版嵁** 涓婏紝浣跨敤涓ユ牸瀛楁绾?Stata/Python 鍙岃窇鍚庯紝渚濈劧鑳界ǔ瀹氬榻愩€?
杩欐槸鈥滅涓€娆℃寮忓紑婧愨€濈殑鏍稿績鍙俊搴﹀伐浣溿€? 
鏈疆浜や粯涓嶆槸闆舵暎楠岃瘉锛岃€屾槸涓€涓彲瀵瑰灞曠ず銆佸彲澶嶆牳銆佸彲鎸佺画鎵╁睍鐨?**OOS 璇佹嵁鍐屽崌绾х増**銆?
## Hard Principles

### 1. No synthetic evidence in this round

杩欎竴杞?**涓嶅厑璁?* 鍐嶇敤 synthetic / controlled toy data 浣滀负涓昏瘉鎹€?
- 鏃?synthetic tests 鍙互浣滀负寮€鍙戞湡鍘嗗彶璧勪骇淇濈暀
- 浣嗗畠浠笉鑳戒綔涓鸿繖杞换鍔″畬鎴愮殑涓诲嚟鎹?- 杩欒疆鐨勪富楠岃瘉蹇呴』鍏ㄩ儴鏉ヨ嚜 **鏂扮殑鍏紑鐪熷疄鏁版嵁**

### 2. No reusing development-time golden tests as the main proof

涓嶅厑璁告妸宸叉湁 `tests/golden/` 鐩存帴閲嶆柊鍖呰鎴愨€滆繖杞殑涓婚獙璇佹垚鏋溾€濄€?
鍏佽锛?- 澶嶇敤鍏叡 helper
- 鍙傝€冩棦鏈夊瓧娈垫瘮杈冮€昏緫
- 鍊熼壌 runner / parser 缁撴瀯

涓嶅厑璁革細
- 鍙妸鏃?test 鏂囦欢澶嶅埗/鏀瑰悕鍚庡绉板畬鎴?- 鍙部鐢ㄨ繃鍘诲凡缁忕敤浜庡紑鍙戞牎鍑嗙殑鏁版嵁闆嗗拰妯″瀷
- 鐢ㄢ€滃紑鍙戞湡宸茬粡璺戣繃鈥濅唬鏇库€滆繖杞?out-of-sample 宸查獙璇佲€?
### 3. Strict field-level alignment remains the gate

杩欒疆缁х画閬靛畧 [docs/validation/validation-policy.md](</D:/OneDrive - SAIF/PhD3/StataFlow/docs/validation/validation-policy.md>)锛?
- 蹇呴』瀛楁绾ф瘮杈?- 涓嶅厑璁稿彧姣旂郴鏁?- 涓嶅厑璁搁€氳繃鏀惧瀹瑰樊鎺╃洊閿欒
- 瀵硅嚜鍔ㄥ甫瀹?/ 鏁板€间紭鍖栬矾寰勶紝濡傞渶鏇村瀹瑰樊锛屽繀椤诲崟鍒楄鏄?
### 4. No estimator feature expansion

鏈疆涓嶆槸鏂板姛鑳借疆銆傞粯璁?**涓嶅厑璁?*锛?
- 鏂板鏂板懡浠?- 鎵╁懡浠ゅ弬鏁伴潰
- 淇敼浼拌鍣ㄦ暟瀛﹂€昏緫
- 涓轰簡璁╂煇涓?OOS case 閫氳繃鑰屽伔鍋锋敼绠楁硶

濡傛灉浣犲彂鐜版煇鍛戒护鍦?OOS 鏁版嵁涓婃毚闇插嚭鐪熷疄 bug锛?
- 鍏堣褰曚负 `blocked`
- 鍦ㄦ姤鍛婁腑鏄庣‘鎸囧嚭
- 涓嶈鍦ㄦ湰杞倓鎮勬敼绠楁硶鎶婇棶棰樻帺鐩栨帀

## Core Objective

寤虹珛涓€濂椻€滄瘡涓凡瀹炵幇鍛戒护鑷冲皯 1 涓柊鐨勫叕寮€鐪熷疄鏁版嵁 baseline + 1 涓柊鐨?variation / stress case鈥濈殑 OOS 楠岃瘉浣撶郴銆?
鑼冨洿瑕嗙洊锛?
- `regress`
- `xtreg, fe`
- `areg`
- `reghdfe`
- `ivregress 2sls`
- `ivreghdfe`
- `logit`
- `probit`
- `poisson`
- `ppmlhdfe`
- `did_imputation`
- `eventstudyinteract`
- `csdid`
- `rdrobust`

## What Counts as Out-of-Sample Here

婊¤冻浠ヤ笅鏉′欢锛屾墠绠?OOS锛?
1. 鏁版嵁闆嗕笉鏄綋鍓嶄富璇佹嵁鍐屼腑宸茬粡浣滀负鏍稿績 dual-run 璇佹嵁浣跨敤鐨勯偅涓€鎵逛富鏍蜂緥銆?2. 妯″瀷璁惧畾涓嶈兘鍙槸澶嶅埗寮€鍙戞湡宸叉湁 case銆?3. 鑷冲皯瑕佽鐩栨柊鍦烘櫙涔嬩竴锛?   - 涓嶅悓鍗忓彉閲忕粍鍚?   - 浜や簰椤?   - 鍥犲瓙鍙橀噺
   - 涓嶅悓 FE 缁撴瀯
   - 涓嶅悓 cluster 閫夋嫨
   - 鏇撮珮缁撮潰鏉?   - 涓嶅悓 link / count / treatment timing 缁撴瀯
   - `rdrobust` 鐨勪笉鍚?bandwidth / covariate usage

濡傛灉鏌愭暟鎹泦浠ュ墠宸茬粡鍦ㄤ粨搴撻噷瀛樺湪锛屼絾浠庢湭浣滀负璇ュ懡浠ょ殑涓?dual-run evidence 浣跨敤锛屼笖鏈疆妯″瀷璁惧畾鏄庢樉涓嶅悓锛屽彲浠ョ畻 OOS銆? 
浣嗕紭鍏堢骇浠嶇劧鏄細**鏂板鍏紑鏁版嵁 > 鏃ф暟鎹柊璁惧畾 > 鏃ц瘉鎹噸澶嶈窇**銆?
## Required Coverage by Family

### A. Linear / FE / HDFE

蹇呴』鏂板鍏紑鐪熷疄闈㈡澘鎴栭珮缁撮潰鏉挎暟鎹紝鑷冲皯瑕嗙洊锛?
- `regress`
- `xtreg, fe`
- `areg`
- `reghdfe`

蹇呴』鑷冲皯鍑虹幇浠ヤ笅鍦烘櫙锛?
1. baseline pooled linear model
2. entity FE
3. absorbed FE
4. 鑷冲皯涓€涓惈浜や簰椤?/ factor-variable 鐨勭湡瀹為潰鏉挎ā鍨?5. 鑷冲皯涓€涓€滀富鏁堝簲琚?absorb 鎺変絾浜や簰椤逛粛鍙瘑鍒€濈殑 `reghdfe` 鍦烘櫙

浼樺厛鏁版嵁绫诲瀷锛?
- firm-year
- county-year
- state-year
- industry-year
- gravity-style panel

### B. IV / Absorbed IV

蹇呴』鏂板鑷冲皯 1 涓叕寮€ IV 鏁版嵁闆嗭紝瑕嗙洊锛?
- `ivregress 2sls`
- `ivreghdfe`

蹇呴』鑷冲皯鍑虹幇浠ヤ笅鍦烘櫙锛?
1. baseline 2SLS
2. absorbed FE + IV
3. 鑷冲皯涓€涓甫浜や簰椤规垨 factor-variable 鐨?IV 璁惧畾锛堝鏋滃懡浠ゅ綋鍓嶆敮鎸侊級

### C. Binary / Count

蹇呴』鏂板鍏紑鐪熷疄鏁版嵁锛岃鐩栵細

- `logit`
- `probit`
- `poisson`
- `ppmlhdfe`

蹇呴』鑷冲皯鍑虹幇浠ヤ笅鍦烘櫙锛?
1. baseline binary response
2. baseline count response
3. 鑷冲皯涓€涓甫浜や簰椤?/ factor-variable 鐨?binary or count model
4. `ppmlhdfe` 鑷冲皯涓€涓浂鍊煎崰姣旈珮銆佸弻鍚?FE 鐨?OOS 鏍蜂緥

### D. DID / Event Study

蹇呴』鏂板鑷冲皯 1 涓叕寮€ staggered adoption 鏁版嵁闆嗭紝瑕嗙洊锛?
- `did_imputation`
- `eventstudyinteract`
- `csdid`

蹇呴』鑷冲皯鍑虹幇浠ヤ笅鍦烘櫙锛?
1. baseline staggered adoption
2. event-study coefficient path
3. cluster inference
4. 鑷冲皯涓€涓笉鍚屼簬褰撳墠 `ezunem` 椋庢牸鐨勭湡瀹炴斂绛?澶勭悊鏃剁偣缁撴瀯

### E. RD

蹇呴』鏂板鑷冲皯 1 涓叕寮€ RD 鏁版嵁闆嗭紝瑕嗙洊锛?
- `rdrobust`

蹇呴』鑷冲皯鍑虹幇浠ヤ笅鍦烘櫙锛?
1. explicit bandwidth
2. automatic bandwidth selection
3. `covs()` 浣跨敤

濡傛灉鏌愬叕寮€ RD 鏁版嵁鍚屾椂閫傚悎澶氫釜璁惧畾锛屽彲浠ュ湪鍚屼竴鏁版嵁闆嗕笂瀹屾垚澶氫釜 case銆?
## Data Sourcing Rules

### Preferred sources

浼樺厛锛?
- 瀹樻柟鏁版嵁浠撳簱
- 璁烘枃澶嶇幇鏁版嵁
- 鏁欏鏁版嵁浠撳簱
- RDatasets
- Stata 瀹樻柟鍏紑鏍蜂緥
- 绀惧尯鍛戒护瀹樻柟浠撳簱鑷甫鍏紑鏁版嵁

### Kaggle rule

Kaggle 涓嶆槸榛樿浼樺厛婧愩€傚彧鏈夊湪浠ヤ笅鏉′欢鍚屾椂婊¤冻鏃舵墠鍙撼鍏ワ細

- 璁稿彲鏄庣‘
- 鏉ユ簮娓呮
- 鐮旂┒鍦烘櫙浠峰€奸珮
- 鑳界ǔ瀹氬鐜颁笅杞借矾寰?
### Mandatory registration

浠讳綍鏂版暟鎹繘鍏ヤ粨搴撳墠锛屽繀椤诲厛鐧昏鍒帮細

- [docs/validation/dataset-registry.md](</D:/OneDrive - SAIF/PhD3/StataFlow/docs/validation/dataset-registry.md>)

姣忎釜鏁版嵁闆嗗繀椤诲啓娓咃細

- 鏉ユ簮缃戝潃
- 涓嬭浇鏂瑰紡
- 鏈湴璺緞
- 璁稿彲 / 鍙垎鍙戞€?- 閫傜敤鍛戒护
- 棰勫鐞嗗叆鍙?- 鏄惁杩涘叆鏈疆 OOS 涓昏瘉鎹泦

## Required Deliverables

### 1. New OOS validation datasets

鍦?`research/data/public/` 涓嬫寜鍛戒护鏃忚ˉ鏂版暟鎹€? 
鍏佽鏂板缓瀛愮洰褰曪紝渚嬪锛?
- `research/data/public/panel/oos/`
- `research/data/public/iv/oos/`
- `research/data/public/binary/oos/`
- `research/data/public/count/oos/`
- `research/data/public/did/oos/`
- `research/data/public/rd/oos/`

### 2. New validation scripts

蹇呴』寤虹珛鐙珛浜庡紑鍙戞湡 golden 娴嬭瘯鐨?OOS runner 浣撶郴銆傚缓璁細

- `scripts/validation/oos/`
  - `run_oos_linear.py`
  - `run_oos_iv.py`
  - `run_oos_glm.py`
  - `run_oos_did.py`
  - `run_oos_rd.py`
  - `run_oos_all.py`

瑕佹眰锛?
- 姣忎釜 runner 閮界湡姝ｈ皟鐢?Stata 涓?Python
- 瀵煎嚭缁撴瀯鍖栫粨鏋?- 涓嶅彧鏄皟鐢ㄦ棫 test 鏂囦欢

### 3. New OOS artifacts

缁熶竴鍐欏埌锛?
- `research/results/validation/oos/`

姣忎釜 case 鑷冲皯浜у嚭锛?
- 缁撴瀯鍖栫粨鏋滄憳瑕侊紙JSON / CSV锛?- 鍙紩鐢ㄧ殑 Markdown 鎽樿

### 4. Evidence-book upgrade

蹇呴』鏇存柊锛?
- [docs/validation/overview.md](</D:/OneDrive - SAIF/PhD3/StataFlow/docs/validation/overview.md)
- [docs/validation/evidence-matrix.md](</D:/OneDrive - SAIF/PhD3/StataFlow/docs/validation/evidence-matrix.md)
- [docs/validation/dataset-registry.md](</D:/OneDrive - SAIF/PhD3/StataFlow/docs/validation/dataset-registry.md)

鏇存柊瑕佹眰锛?
- 鏄庣‘鍖哄垎 `development-time validation` 涓?`out-of-sample validation`
- 杩欒疆鏂板鐨?OOS 璇佹嵁蹇呴』鍗曠嫭鏍囪瘑
- 姣忎釜鍛戒护鐨勮瘉鎹」瑕佽兘杩芥函鍒版暟鎹€佽剼鏈€佺粨鏋滄枃浠?
### 5. Release-facing entry point

蹇呴』鎶?OOS 璇佹嵁鍏ュ彛鎺ュ埌锛?
- `README.md`
- 濡傛湁闇€瑕侊紝`docs/release/open-source-alpha-status.md`

璁╁閮ㄧ敤鎴疯兘鐩存帴鐪嬪埌锛?
- 褰撳墠鍛戒护鏄惁缁忚繃 OOS 楠岃瘉
- 楠岃瘉鍒颁粈涔堢▼搴?- 鍝簺浠嶆槸 validated subset

## Explicit Prohibitions

浠ヤ笅鍋氭硶鏈疆鏄庣‘绂佹锛?
- 鐢?synthetic 鏁版嵁琛ヨ瘉鎹己鍙?- 鐩存帴鎶婂凡鏈?`tests/golden` 澶嶅埗鍚庡綋鏈疆涓绘垚鏋?- 涓轰簡璁?OOS case 杩囪€屼慨鏀逛及璁″櫒绠楁硶
- 鍙瘮绯绘暟涓嶆瘮鎺ㄦ柇
- 鐢ㄥ崟涓€鏁版嵁闆嗚鐩栧叏閮ㄥ懡浠ゅ悗瀹ｇО鈥滃叏闈?validation鈥?- 鐢?README 鎵嬪伐闄堣堪鏇夸唬缁撴瀯鍖栬瘉鎹骇鐗?
## Acceptance Standard

Codex 鍙細鍦ㄤ互涓嬫潯浠堕兘婊¤冻鏃舵斁琛岋細

1. 姣忎釜鍛戒护鑷冲皯鏈?1 涓柊鐨?OOS real-data evidence case
2. 姣忎釜鍛戒护鏃忚嚦灏戞湁 1 涓?variation / stress case
3. 鏂拌瘉鎹笉鍐嶄緷璧?synthetic 涓昏矾寰?4. OOS runner 涓庣粨鏋滀骇鐗╃嫭绔嬪瓨鍦紝鍙璺?5. evidence matrix銆乨ataset registry銆丷EADME 鍏ュ彛鍚屾鏇存柊
6. 瀵规瘡涓懡浠ら兘鑳芥槑纭垽鏂細
   - `passed`
   - `passed_with_documented_tolerance`
   - `partial_subset`
   - `blocked`

## Reporting Format

瀹屾垚鍚庡湪 [workspace/current-task/REPORT.md](</D:/OneDrive - SAIF/PhD3/StataFlow/workspace/current-task/REPORT.md>) 鎸変互涓嬬粨鏋勬眹鎶ワ細

1. 鏂板浜嗗摢浜涘叕寮€鏁版嵁
2. 姣忎釜鍛戒护鏂板浜嗗摢浜?OOS case
3. 姣忎釜鍛戒护鏃忕殑 baseline / variation / stress case 鏄粈涔?4. 杩愯浜嗗摢浜?OOS runner
5. 鐢熸垚浜嗗摢浜涚粨鏋勫寲缁撴灉浜х墿
6. 鍝簺鍛戒护 `passed`
7. 鍝簺鍛戒护 `partial_subset`
8. 鍝簺鍛戒护 `blocked`
9. 褰撳墠杩欒疆 OOS 璇佹嵁鏄惁瓒充互浣滀负棣栨寮€婧愮増鏈€滆縼绉绘垚鍔熶笖鍑嗙‘鈥濈殑鏍稿績璇存槑
