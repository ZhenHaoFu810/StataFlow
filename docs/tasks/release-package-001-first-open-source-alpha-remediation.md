# 鍙戝竷浠诲姟鍖?001锛氶娆″紑婧?Alpha 淇籍

## 浠诲姟瀹氫綅

鏈疆涓嶆槸绠楁硶鎵╁睍杞紝涔熶笉鏄?vendor 鍛戒护瀹屾暣搴︽帹杩涜疆銆? 
鏈疆鐩爣鍙湁涓€涓細

> 鎶婂綋鍓嶄粨搴撲粠鈥滈珮璐ㄩ噺 Alpha锛屼絾鏇村儚鍐呴儴鐮旂┒浠撳簱鈥濇帹杩涘埌鈥滈€傚悎绗竴娆℃寮忓澶栧紑婧愬睍绀轰笌璇曠敤鈥濈殑鐘舵€併€?
浣?*涓嶉渶瑕佹柊澧炰换浣曚及璁″櫒鍔熻兘**锛屼篃**涓嶅厑璁?*椤烘墜鎵╁懡浠ら潰銆? 
鎵€鏈夊伐浣滈兘鍥寸粫鈥滈娆″紑婧愬彂甯冮潰淇籍鈥濆睍寮€銆?
## 蹇呴』浣跨敤鐨勪緷鎹?
鍏堣骞朵弗鏍奸伒瀹堜互涓嬫枃妗ｏ細

1. [docs/qa/first-open-source-release-review.md](</D:/OneDrive - SAIF/PhD3/StataFlow/docs/qa/first-open-source-release-review.md>)
2. [docs/qa/first-open-source-release-issues.md](</D:/OneDrive - SAIF/PhD3/StataFlow/docs/qa/first-open-source-release-issues.md>)
3. [docs/qa/first-open-source-release-remediation-plan.md](</D:/OneDrive - SAIF/PhD3/StataFlow/docs/qa/first-open-source-release-remediation-plan.md>)
4. [docs/operations/executor-playbook.md](</D:/OneDrive - SAIF/PhD3/StataFlow/docs/operations/executor-playbook.md>)
5. [docs/operations/codex-review-protocol.md](</D:/OneDrive - SAIF/PhD3/StataFlow/docs/operations/codex-review-protocol.md>)

## 鐩爣

鏈疆蹇呴』鑷冲皯瀹屾垚浠ヤ笅涓夊ぇ鍧楋細

### A. 鍙戝竷闃诲椤规敹鍙?
蹇呴』淇帀浠ヤ笅纭樆濉烇細

1. 鏍圭洰褰曠己灏?`LICENSE`
2. `pyproject.toml` 鍏冩暟鎹笉瀹屾暣
3. README 涓?`pyproject.toml` 鐨?Python 鐗堟湰瑕佹眰涓嶄竴鑷?4. release-facing 鏂囨。涓殑閿欒 issue / 浠撳簱閾炬帴

### B. 浠撳簱鏁存磥搴︿慨缂?
蹇呴』鏁寸悊棣栨寮€婧愮殑浠撳簱琛ㄩ潰锛?
1. 鏍圭洰褰曟棩蹇楁枃浠跺鐞嗘帀
2. 鏄庢樉鍐呴儴 / 涓€娆℃€ц剼鏈縼绉诲埌鏇村悎閫傜洰褰曪紝鎴栨槑纭綊妗?3. `.gitignore` 鏇存柊鍒颁笌褰撳墠浠撳簱褰㈡€佷竴鑷?4. README 涓?`examples/` 鐨勫叆鍙ｅ叧绯绘竻妤?
### C. 宸ョ▼鍖栨渶浣庝繚闅?
蹇呴』琛ユ渶灏忓伐绋嬪寲淇″彿锛?
1. 鏂板鍩虹 CI workflow
2. workflow 鑷冲皯瑕嗙洊锛?   - 瀹夎
   - import / smoke
   - 鍏ㄩ噺 pytest

濡備綘璁や负鍚堢悊锛屼篃鍙互琛ワ細

3. `CONTRIBUTING.md`
4. 绠€鐭?release note / publishing note

## 蹇呴』閲嶇偣淇殑鍏蜂綋闂

### 1. LICENSE

浣犲繀椤绘柊澧炰竴涓寮忚鍙瘉鏂囦欢銆?
瑕佹眰锛?
- 璁稿彲璇佺被鍨嬪繀椤绘槑纭啓鍦ㄦ枃浠朵腑
- `pyproject.toml` 涓?README / release 鏂囨。鍙ｅ緞涓€鑷?
濡傞」鐩不鐞嗘枃妗ｆ湭鏄庣‘鎸囧畾璁稿彲璇侊紝鍙厛閲囩敤涓€涓竻鏅般€佸鏉俱€侀€傚悎棣栨寮€婧愮殑璁稿彲璇侊紝骞跺湪鎶ュ憡涓鏄庨€夋嫨鐞嗙敱銆?
### 2. `pyproject.toml`

鑷冲皯琛ラ綈锛?
- `readme`
- `license`
- `authors` 鎴?`maintainers`
- `classifiers`
- `keywords`
- `urls`

骞剁‘淇濊繖浜涘厓鏁版嵁涓?README 瀵瑰琛ㄨ堪涓€鑷淬€?
### 3. Python 鐗堟湰鍙ｅ緞缁熶竴

褰撳墠宸茬煡涓嶄竴鑷达細

- README 璇?`Python 3.9+`
- `pyproject.toml` 璇?`>=3.10`

浣犲繀椤荤粺涓€銆?
瑕佹眰锛?
- 涓嶅厑璁稿彧鏀瑰叾涓竴涓湴鏂硅€屼笉楠岃瘉
- 濡傝涓嬭皟鍒?3.9锛屽繀椤绘湁璇佹嵁锛涘惁鍒欑粺涓€鎻愬崌鍒?3.10+

### 4. release-facing 閿欒閾炬帴

淇帀浠讳綍鎸囧悜閿欒浠撳簱 / issue 椤电殑閾炬帴銆?
濡傛灉杩樻病鏈夋寮忓叕寮€ issue 鍦板潃锛?
- 涓嶈纭～閿欒鍦板潃
- 鍙互鏀规垚鍗犱綅璇存槑鎴栦粨搴撲富椤?
### 5. 鏍圭洰褰曞櫔闊?
褰撳墠鏍圭洰褰曞瓨鍦ㄥ绉嶄笉閫傚悎棣栨寮€婧愭毚闇茬殑鏂囦欢銆?
浣犲繀椤诲鐞嗭細

- `.log`
- 涓存椂杩愯鑴氭湰
- 涓€娆℃€ц瘖鏂剼鏈?
鍘熷垯锛?
- 鑳借縼绉诲氨杩佺Щ鍒版竻鏅扮洰褰?- 涓嶈杩涚増鏈帶鍒剁殑灏卞姞鍏?`.gitignore`
- 涓嶈鍒犳帀鐪熸浠嶆湁浠峰€肩殑鐮旂┒/杈呭姪鑴氭湰锛屼絾瑕佽瀹冧滑涓嶅啀姹℃煋鏍圭洰褰?
### 6. CI workflow

鑷冲皯鏂板涓€涓熀纭€ workflow锛屼緥濡傦細

- install dependencies
- run example smoke or import smoke
- run `python -m pytest tests -v`

瑕佹眰锛?
- 宸ヤ綔娴佽涔夋竻妤?- 涓嶈鍐欐垚鏃犳硶鎵ц鐨勬憜璁?- 濡?golden tests 渚濊禆鏈湴 Stata锛岄渶璇存槑鏄惁鍦?CI 涓叏閮ㄨ窇锛屾垨濡備綍鍒嗗眰璺宠繃

## 鍏佽淇敼鐨勬枃浠?
浣犲彲浠ヤ慨鏀规垨鏂板锛?
- `LICENSE`
- `pyproject.toml`
- `README.md`
- `docs/release/*`
- `.gitignore`
- `.github/workflows/*`
- `examples/*`
- `docs/qa/*`锛堝闇€鍥炲～锛?- 鏍圭洰褰曞唴閮ㄨ剼鏈笌鍏惰縼绉荤洰鏍囩洰褰?
## 鏄庣‘绂佹

- 涓嶆柊澧炰换浣曚及璁″櫒鍔熻兘
- 涓嶆敼 `reghdfe` / `ppmlhdfe` / `ivreghdfe` / DID / `rdrobust` 绠楁硶閫昏緫
- 涓嶆妸鈥滀慨鏂囨。鈥濇墿鎴愨€滈『鎵嬮噸鏋勬暣涓唬鐮佸簱鈥?- 涓嶄负浜嗚鏍圭洰褰曟洿骞插噣鑰屽垹鎺夌湡姝ｆ湁浠峰€间絾灏氭湭褰掓。鐨勬枃浠讹紝闄ら潪宸茶縼绉?
## 鏈€浣庨獙璇佽姹?
鏈疆鑷冲皯瑕佽窇锛?
```powershell
python -m pip wheel . --no-deps -w .codex_tmp_dist
python -m pytest tests -v
python examples/demo_regress.py
python examples/demo_reghdfe.py
python examples/demo_ppmlhdfe.py
python examples/demo_ivregress_2sls.py
```

濡傛柊澧炴垨淇敼 CI workflow锛岃鍦ㄦ姤鍛婁腑璇存槑鍏惰鐩栬寖鍥翠笌灞€闄愩€?
## 閫氳繃鏍囧噯

Codex 鍙細鍦ㄤ互涓嬫潯浠堕兘婊¤冻鏃舵斁琛岋細

1. 棣栨寮€婧愮殑纭樆濉為」锛圠ICENSE銆佸厓鏁版嵁銆佺増鏈姹傘€侀敊璇摼鎺ワ級宸叉敹鍙?2. 鏍圭洰褰曟槑鏄炬洿鏁存磥锛屼复鏃惰剼鏈?鏃ュ織涓嶅啀鐩存帴姹℃煋浠撳簱棣栭〉
3. 鑷冲皯鏈変竴涓熀纭€ CI workflow
4. wheel 浠嶈兘鏋勫缓
5. 鍏ㄩ噺娴嬭瘯涓庢牳蹇?example smoke 浠嶉€氳繃
6. 鏂囨。涓庡疄闄呭澶栧彂甯冮潰涓€鑷达紝涓嶅じ澶с€佷笉鐣欐槑鏄鹃敊璇摼鎺?
## 鍥炴姤鏍煎紡

瀹屾垚鍚庡湪 [workspace/current-task/REPORT.md](</D:/OneDrive - SAIF/PhD3/StataFlow/workspace/current-task/REPORT.md>) 涓寜涓嬮潰缁撴瀯鍥炴姤锛?
1. 淇帀浜嗗摢浜?release-blocking 闂
2. `pyproject.toml` / README / release 鏂囨。濡備綍缁熶竴浜?3. 鏍圭洰褰曞摢浜涙枃浠惰杩佺Щ銆佹竻鐞嗘垨褰掓。
4. 鏂板浜嗗摢浜?CI / release-facing 鏂囦欢
5. 璺戜簡鍝簺楠岃瘉鍛戒护
6. 鏈€鏂?fresh run 缁撴灉
7. 褰撳墠浠撳簱鏄惁宸茶揪鍒扳€滈€傚悎绗竴娆℃寮忓澶栧紑婧?Alpha 鍙戝竷鈥濈殑鏍囧噯
