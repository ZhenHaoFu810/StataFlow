# 椤圭洰涓ユ牸瀹¤鎶ュ憡

## 1. 瀹¤鑼冨洿

鏈瀹¤闈㈠悜褰撳墠浠撳簱鐨勨€滃紑婧愮涓夋柟搴撳垵鐗堚€濇暣浣撶姸鎬侊紝閲嶇偣妫€鏌ワ細

- `research/vendor/stata_community/` 涓嬪紑婧?Stata 绀惧尯鍛戒护鐨勫鐜板畬鏁村害涓庢纭€?- `src/stataflow/compat/stata/` 鍛戒护灞傛帴鍙ｆ槸鍚︿笌 Stata 璇箟涓€鑷?- core estimator銆亀rapper銆佹枃妗ｃ€佹祴璇曚笁鑰呮槸鍚︿竴鑷?- 褰撳墠浠ｇ爜鏄惁杈惧埌鈥滃彲鍏紑鍙戝竷鐨勫垵鐗堝簱鈥濇爣鍑?
鏈瀹¤涓嶄互鈥滄祴璇曟槸鍚﹀叏缁库€濅綔涓哄敮涓€鍒ゆ柇鏍囧噯锛岃€屼互锛?
1. 婧愮爜/鎵嬪唽鏀拺涓嬬殑鏁板涓庤閲忚繃绋嬩竴鑷存€? 
2. 鍛戒护璇箟涓庡弬鏁伴潰鐨勫畬鏁存€? 
3. 鏂囨。銆佹帴鍙ｃ€佺粨鏋滃璞′笌琛屼负鐨勪竴鑷存€? 

涓轰富鍒ゆ柇渚濇嵁銆?
## 2. 瀹¤鐜涓庨獙璇佸懡浠?
### 鐜

- OS: Windows
- Python: `3.11.7`
- 瑙ｉ噴鍣? `C:\ProgramData\anaconda3\python.exe`
- 宸ヤ綔鐩綍: `D:\OneDrive - SAIF\PhD3\StataFlow`
- Stata 鐩爣鐗堟湰: 17

### 鏈疆瀹為檯鎵ц鐨勯獙璇?
#### 鍩虹嚎娴嬭瘯

```powershell
python -m pytest tests -v
```

缁撴灉锛?
- `681 passed in ~150s`

#### 绀轰緥鑴氭湰鎶芥煡

```powershell
python examples/demo_regress.py
python examples/demo_reghdfe.py
python examples/demo_ppmlhdfe.py
python examples/demo_ivregress_2sls.py
```

缁撴灉锛?
- 鍥涗釜绀轰緥鍧囧彲杩愯

#### 缁撴瀯涓庡疄鐜版娊鏌?
宸叉牳瀵癸細

- `src/stataflow/compat/stata/__init__.py`
- `src/stataflow/compat/stata/linear.py`
- `src/stataflow/compat/stata/hdfe.py`
- `src/stataflow/compat/stata/iv.py`
- `src/stataflow/compat/stata/glm.py`
- `src/stataflow/compat/stata/did.py`
- `docs/command-support-matrix/*`
- `docs/research/*-source-map.md`
- `research/vendor/stata_community/*`

## 3. 鍏ㄥ簱鎬讳綋缁撹

### 缁撹鎽樿

褰撳墠浠撳簱宸茬粡鏄竴涓?*楂樿川閲忋€佸己楠岃瘉銆佸彲杩愯鐨?Stata 瀵归綈鍨嬭閲忓簱 Alpha 鐗堟湰**锛屼絾**灏氫笉鑳借璁ゅ畾涓衡€滃叏闈㈠畬鎴愮殑 Stata 寮€婧愬懡浠ゅ畬鏁村鐜板簱鈥?*銆?
鏇村噯纭殑瀹氫綅鏄細

- 鏁板€间笌缁熻缁撴灉瀵归綈妗嗘灦宸茬粡鎴愮啛
- 楂樹环鍊煎懡浠ょ殑楂橀璺緞宸插ぇ闈㈢Н瀹炵幇骞堕€氳繃 synthetic + real-data 鍙岀嚎楠岃瘉
- 鍛戒护灞?API 宸茬粡鏄捐憲鏀瑰杽锛屽彲鐩存帴浣跨敤 Stata 椋庢牸 wrapper
- 浣?`vendor` 涓嬬ぞ鍖哄懡浠ゆ暣浣撲粛涓昏鍋滅暀鍦ㄢ€滈珮棰戝瓙闆?+ 娓呮櫚杈圭晫 + 寮烘祴璇曗€濈殑闃舵锛岃€屼笉鏄€滃畬鏁村懡浠ょ骇澶嶇幇鈥?
### 鍙戝竷鍒ゆ柇

鎸夆€滅爺绌跺瀷 Alpha / 鎶€鏈鍙戝竷鈥濈殑鏍囧噯锛?*鍩烘湰鍙彂甯?*銆? 
鎸変綘褰撳墠瑕佹眰鐨勬洿涓ユ牸鏍囧噯锛屽嵆锛?
- `vendor` 涓嬪紑婧愬懡浠ゅ繀椤诲畬鏁淬€佸叏闈€佹纭鐜?- 涓嶈兘鎺ュ彈鍙疄鐜版牳蹇冭矾寰勮€岄潪瀹屾暣鍛戒护

鍒欏綋鍓嶇増鏈?*涓嶆弧瓒虫渶缁堟爣鍑?*锛屽師鍥犺鍚庢枃銆?
## 4. 鍒嗗懡浠ょ粨璁烘€昏〃

### 4.1 Vendor 寮€婧愬懡浠ゅ璁¤〃

| 鍛戒护 | Python 鍏ュ彛 | wrapper 鍏ュ彛 | 娴嬭瘯鐘舵€?| 瀹¤璇勭骇 | 缁撹 |
| --- | --- | --- | --- | --- | --- |
| `reghdfe` | `AbsorbingOLS` | `stataflow.compat.stata.reghdfe` | synthetic + real-data 閫氳繃 | `partial` | 鏍稿績璺緞鎴愮啛锛屼絾涓嶆槸瀹屾暣 `reghdfe` |
| `ivreghdfe` | `IVAbsorbingOLS` | `stataflow.compat.stata.ivreghdfe` | synthetic + real-data 閫氳繃 | `partial` | 2SLS + FE 涓昏矾寰勫彲鐢紝浣嗗懡浠ら潰鏄庢樉涓嶅畬鏁?|
| `ppmlhdfe` | `PPMLHDFE` | `stataflow.compat.stata.ppmlhdfe` | synthetic + real-data 閫氳繃 | `partial` | PPML-HDFE 涓昏矾寰勫彲鐢紝浣?separation 绛夊叧閿姛鑳芥湭瀹屾垚 |
| `did_imputation` | `DIDImputation` | `stataflow.compat.stata.did_imputation` | synthetic + real-data 閫氳繃 | `partial` | 鍩烘湰 BJS 璺緞鍙敤锛屼絾鍙傛暟闈㈣繙鏈畬鏁?|
| `eventstudyinteract` | `EventStudyInteract` | `stataflow.compat.stata.eventstudyinteract` | synthetic + real-data 閫氳繃 | `partial` | IW 浼拌鏍稿績鍙敤锛屼絾鍛戒护闈粛鏄瓙闆?|
| `rdrobust` | `RDRobust` | `stataflow.compat.stata.rdrobust` | synthetic + real-data 閫氳繃 | `partial` | Sharp RD 鏈€灏忓瓙闆嗗彲鐢紙闇€鏄惧紡甯﹀锛夛紝鑷姩甯﹀閫夋嫨銆佹ā绯?RD銆佸崗鍙橀噺鏈疄鐜?|

### 4.2 鍏朵粬楂橀鍛戒护缁撹

| 鍛戒护 | 瀹¤璇勭骇 | 缁撹 |
| --- | --- | --- |
| `regress` | `strong_subset` | 楂橀绾挎€у洖褰掕矾寰勬垚鐔燂紝浣嗘潈閲嶇被鍨嬪拰瀹屾暣鍛戒护闈㈡湭瀹屾垚 |
| `xtreg, fe` | `strong_subset` | 鍗?FE within 璺緞鎴愮啛锛屼粛闈炲畬鏁?`xtreg` |
| `areg` | `strong_subset` | 鍗曞惛鏀?FE 鍛戒护璇箟娓呮锛屽彲绋冲畾浣跨敤 |
| `ivregress 2sls` | `strong_subset` | 2SLS 楂橀璺緞鎴愮啛锛屼絾璇婃柇宸ュ叿閾句笉瀹屾暣 |
| `logit` / `probit` / `poisson` | `strong_subset` | MLE 楂橀璺緞鎴愮啛锛寃rapper 娓呮锛屽畬鏁村懡浠ら潰鏈畬鎴?|
| `csdid` | `partial` | `method="reg"` 璺緞鎴愮啛锛屼絾涓嶆槸瀹屾暣 `csdid` |
| `predict` / `margins` 楂橀瀛愰泦 | `strong_subset` | 鏍稿績灞傚彲鐢紝wrapper 灞備笉鐩存帴鏆撮湶锛岃竟鐣屽凡娓呮 |

## 5. Vendor 鍛戒护閫愰」缁撹

### 5.1 `reghdfe`

#### 宸茬‘璁ゆ垚绔?
- 鏈夋湰鍦版簮鐮侀暅鍍忎笌 source map
- 宸叉湁姝ｅ紡 wrapper锛歚stataflow.compat.stata.reghdfe`
- 宸查€氳繃 synthetic 涓?real-data 鍙岀嚎楠岃瘉
- 宸插疄鐜板苟楠岃瘉锛?  - `absorb()` 1-2 涓垎绫?FE
  - `vce(ols)` / `vce(robust)` / `vce(cluster)`
  - singleton 榛樿鍓旈櫎
  - 鍩虹 `df_a`
  - `predict(xb)` / `predict(residuals)` 鍦?core estimator 灞?
#### 涓嶈兘璁ゅ畾涓哄畬鏁村鐜扮殑鍘熷洜

- 浠呮敮鎸?1-2 涓垎绫?FE锛屼笉瓒充互瑕嗙洊鐢ㄦ埛閫氬父鐞嗚В鐨勨€滈珮缁村浐瀹氭晥搴斿畬鏁翠换鍔♀€?- 鏈畬鎴?mobility-group 绛夋洿澶嶆潅 DoF 閫昏緫
- 鏈敮鎸?slopes銆乮ndividual/group/team FE 绛夋洿瀹屾暣鍛戒护闈?- 涓嶆敮鎸?multi-way clustering
- `keepsingletons` 绛夊叧閿€夐」鏈毚闇?- postestimation 涓嶆槸鍛戒护灞傚畬鏁村鐜?
#### 瀹¤鍒ゆ柇

`reghdfe` 褰撳墠鏄?*楂樿川閲忕殑 Phase A 瀛愰泦瀹炵幇**锛屼笉鏄畬鏁淬€佸叏闈㈠鐜般€?
### 5.2 `ivreghdfe`

#### 宸茬‘璁ゆ垚绔?
- 鏈夋湰鍦版簮鐮侀暅鍍忎笌 source map
- 鏈夋寮?wrapper
- 宸查€氳繃 synthetic 涓?real-data 楠岃瘉
- 宸叉敮鎸?2SLS + 1-2 FE + robust/cluster 楂橀璺緞

#### 涓嶈兘璁ゅ畾涓哄畬鏁村鐜扮殑鍘熷洜

- 浠呰鐩栨渶灏?2SLS 璺緞
- first-stage 鎶ュ憡銆佸急宸ュ叿璇婃柇銆佽繃璇嗗埆妫€楠岀瓑宸ュ叿閾炬湭瀹屾垚
- 鏇村箍鐨勫懡浠ら€夐」闈㈡湭瀹屾垚
- multi-way cluster 鏈畬鎴?
#### 瀹¤鍒ゆ柇

`ivreghdfe` 褰撳墠鏄?*鍙敤鐨勬渶灏忓瓙闆嗗疄鐜?*锛屼笉鏄畬鏁?`ivreghdfe`銆?
### 5.3 `ppmlhdfe`

#### 宸茬‘璁ゆ垚绔?
- 鏈夋湰鍦版簮鐮侀暅鍍忎笌 source map
- 鏈夋寮?wrapper
- 宸查€氳繃 synthetic 涓?gravity 椋庢牸鐪熷疄鏁版嵁楠岃瘉
- 宸叉敮鎸侊細
  - `absorb()`
  - `vce(ols)` / `vce(robust)` / `vce(cluster)`
  - `offset` / `exposure`
  - `predict(xb)` / `predict(mu)` 鍦?core estimator 灞?
#### 涓嶈兘璁ゅ畾涓哄畬鏁村鐜扮殑鍘熷洜

- separation 妫€娴嬪皻鏈疄鐜帮紝鑰岃繖鎭版伆鏄?`ppmlhdfe` 鐨勫叧閿鏉傜偣涔嬩竴
- `deviance` / `pseudo R2` / `LR chi2` 绛夎緭鍑哄眰涓嶅畬鏁?- `predict residuals` 鏈疄鐜?- 鍛戒护鍙傛暟闈㈣繙涓嶅畬鏁?- multi-way cluster 鏈畬鎴?
#### 瀹¤鍒ゆ柇

`ppmlhdfe` 褰撳墠鏄?*寮哄彲鐢ㄧ殑楂橀涓昏矾寰勫疄鐜?*锛屼絾涓嶆槸瀹屾暣绀惧尯鍛戒护澶嶇幇銆?
### 5.4 `did_imputation`

#### 宸茬‘璁ゆ垚绔?
- 鏈夋湰鍦版簮鐮侀暅鍍忎笌 source map
- 鏈夋寮?wrapper
- synthetic 涓庣湡瀹炴暟鎹潎宸查€氳繃
- `cluster`銆乣allhorizons`銆乣autosample` 鍙敤

#### 涓嶈兘璁ゅ畾涓哄畬鏁村鐜扮殑鍘熷洜

- `minn`銆乣window`銆乣pretrend` 绛夊弬鏁伴潰鏈畬鎴?- FE / truncation 绛夋洿瀹屾暣鍛戒护琛屼负鏈敮鎸?
#### 瀹¤鍒ゆ柇

鏄竴涓?*鏍稿績璺緞宸插畬鎴愮殑瀛愰泦瀹炵幇**锛屼笉鏄畬鏁村懡浠ゃ€?
### 5.5 `eventstudyinteract`

#### 宸茬‘璁ゆ垚绔?
- 鏈夋湰鍦版簮鐮侀暅鍍忎笌 source map
- wrapper 宸叉敮鎸佽嚜鍔ㄧ敓鎴?relative-time dummies
- synthetic 涓庣湡瀹炴暟鎹獙璇侀€氳繃

#### 涓嶈兘璁ゅ畾涓哄畬鏁村鐜扮殑鍘熷洜

- `window`銆乣minn` 绛夊弬鏁版湭瀹屾垚
- 缁撴灉杈撳嚭涓庢墿灞曞懡浠ら潰涓嶅畬鏁?- 铏界劧 wrapper 宸茶緝鎺ヨ繎鍛戒护璇箟锛屼絾浠嶆槸楂橀鍦烘櫙瀵煎悜鐨勫瓙闆?
#### 瀹¤鍒ゆ柇

鏄竴涓?*鐩稿綋瀹炵敤鐨?IW 瀛愰泦瀹炵幇**锛屼絾涓嶆槸瀹屾暣澶嶇幇銆?
### 5.6 `rdrobust`

#### 宸茬‘璁ゆ垚绔?
- 宸叉湁鏈湴婧愮爜闀滃儚锛歚research/vendor/stata_community/rdrobust/`
- 宸插疄鐜版渶灏忓瓙闆嗭細`RDRobust` estimator + `rdrobust` wrapper
- 鏀寔 sharp RD锛坄deriv=0`锛夌殑灞€閮ㄥ椤瑰紡 WLS + 鍋忓樊淇 + 绋冲仴鎺ㄦ柇
- 鏀寔鏄惧紡甯﹀ `h`銆佹牳鍑芥暟閫夋嫨銆乣vce="nn"` / `vce="hc0"`
- 宸查€氳繃 synthetic 鍜?`rdrobust_senate.dta` 鐪熷疄鏁版嵁 dual-run 楠岃瘉

#### 涓嶈兘璁ゅ畾涓哄畬鏁村鐜扮殑鍘熷洜

- 涓嶆敮鎸佽嚜鍔ㄥ甫瀹介€夋嫨锛坄bwselect` 绛夛級锛屽繀椤绘樉寮忔彁渚?`h`
- 涓嶆敮鎸佹ā绯?RD锛坄fuzzy`锛?- 涓嶆敮鎸佸崗鍙橀噺璋冩暣锛坄covs`锛?- 涓嶆敮鎸?`deriv > 0`锛坘ink designs锛?- 涓嶆敮鎸佹潈閲嶅拰鑱氱被绋冲仴 VCE

#### 瀹¤鍒ゆ柇

`rdrobust` 褰撳墠鏄?*鏈€灏忓彲鐢ㄥ瓙闆嗗疄鐜?*锛屼笉鏄畬鏁寸ぞ鍖哄懡浠ゅ鐜般€?
## 6. 浠ｇ爜璐ㄩ噺銆佺ǔ瀹氭€т笌鍙敤鎬у垽鏂?
### 6.1 浠ｇ爜璐ㄩ噺

鎬讳綋鍒ゆ柇锛?*涓珮姘村钩锛屽伐绋嬬粨鏋勬竻妤氾紝瀹℃煡涓庢祴璇曟枃鍖栨槑鏄句紭浜庝竴鑸爺绌跺瀷浠撳簱銆?*

浼樼偣锛?
- estimator / wrapper / docs / golden tests 鍒嗗眰娓呮
- 鍛戒护灞?wrapper 宸蹭笌 core estimator 瑙ｈ€?- unsupported 鍙傛暟鏅亶鏄樉寮忔姤閿欙紝鑰屼笉鏄潤榛樺拷鐣?- source map 涓?support matrix 浣撶郴宸茬粡褰㈡垚

涓昏淇濈暀鎰忚锛?
- 涓埆 core estimator 浠嶅悓鏃舵壙杞藉涓懡浠よ涔夛紝渚嬪 `AbsorbingOLS`
- 涓€浜涒€滃畬鏁村懡浠も€濆湪鏂囨。涓婂凡缁忓啓寰楀緢娓呮鏄?`Alpha`锛屼絾浠庝骇鍝佺洿瑙変笂浠嶅鏄撹璇敤涓衡€滃凡瀹屾暣鏀寔鈥?
### 6.2 绋冲畾鎬?
鎬讳綋鍒ゆ柇锛?*寮恒€?*

璇佹嵁锛?
- 鍏ㄩ噺 `489` 涓祴璇曢€氳繃
- wrapper銆乬olden銆乺eal-data銆乸ostestimation 閮藉凡绾冲叆鍥炲綊闆?- 绀轰緥鑴氭湰鍙繍琛?
淇濈暀鎰忚锛?
- 娴嬭瘯瑕嗙洊寰堝己锛屼絾褰撳墠瑕嗙洊鐨勬槸鈥滃凡瀹ｇО鏀寔鐨勫姛鑳借竟鐣屸€?- 娴嬭瘯鍏ㄧ豢骞朵笉绛変簬鍛戒护瀹屾暣澶嶇幇

### 6.3 鏄撶敤鎬?
鎬讳綋鍒ゆ柇锛?*鏄捐憲浼樹簬姝ゅ墠鐗堟湰锛屼絾浠嶆湭杈惧埌鈥滄棤 Stata 鑳屾櫙涔熻兘涓€鐪兼槑鐧藉畬鏁存敮鎸佽寖鍥粹€濈殑绋嬪害銆?*

浼樼偣锛?
- `compat.stata` wrapper 灞傚凡缁忚В鍐充簡澶ч儴鍒嗗懡浠ゅ懡鍚嶉棬妲?- README 涓?support matrix 宸茬粡璇存槑 wrapper 涓嶇洿鎺ユ毚闇?`predict` / `margins`

闂锛?
- wrapper 鍚嶇О涓?Stata 瀵归綈浜嗭紝浣嗏€滃畬鏁村懡浠?vs 瀛愰泦瀹炵幇鈥濈殑杈圭晫浠嶉渶瑕佺敤鎴疯鏂囨。鎵嶆竻妤?- 缂哄皯涓€浠介潰鍚戝閮ㄥ紑婧愮敤鎴风殑鈥滃凡瀹屾暣鏀寔 / 浠呭瓙闆嗘敮鎸?/ 灏氭湭瀹炵幇鈥濇€昏缁撹

## 7. 鏈€缁堝垽鏂?
### 鎸夊鏉炬爣鍑?
濡傛灉鏍囧噯鏄細

- 浣滀负涓€涓彲杩愯銆佸己楠岃瘉銆丼tata 瀵归綈瀵煎悜鐨?Python 璁￠噺搴?Alpha 鐗堟湰

鍒欏綋鍓嶉」鐩?*宸茬粡杈惧埌杈冮珮璐ㄩ噺姘村钩**銆?
### 鎸変綘褰撳墠缁欏嚭鐨勪弗鏍兼爣鍑?
濡傛灉鏍囧噯鏄細

- `research/vendor/stata_community` 涓嬭繖浜涘紑婧愬懡浠ゅ繀椤诲凡缁忚**瀹屾暣銆佸叏闈€佹纭?*澶嶇幇
- 涓嶈兘鎺ュ彈鈥滃彧瀹炵幇鏍稿績鍔熻兘浣嗕笉鏄畬鏁村懡浠も€?
鍒欏綋鍓嶉」鐩?*鏈揪鍒版爣鍑?*銆?
鏍规湰鍘熷洜涓嶆槸浠ｇ爜宸紝涔熶笉鏄祴璇曞樊锛岃€屾槸锛?
- `reghdfe`
- `ivreghdfe`
- `ppmlhdfe`
- `did_imputation`
- `eventstudyinteract`
- `csdid`
- `rdrobust`

閮戒粛鏄?*楂橀涓昏矾寰?鏍稿績瀛愰泦澶嶇幇**锛屼笉鏄畬鏁村懡浠ゅ鐜般€?
鍥犳锛屽綋鍓嶆洿鍚堢悊鐨勫閮ㄨ〃杩板簲鏄細

> 杩欐槸涓€涓粡杩囦弗鏍奸獙璇佺殑 Stata 瀵归綈鍨?econometrics library Alpha锛屽凡瑕嗙洊澶氱被楂橀鍛戒护鐨勯珮棰戣矾寰勶紝浣嗗皻鏈畬鎴愬鎵€鏈夌ぞ鍖哄懡浠ょ殑瀹屾暣澶嶇幇銆?
