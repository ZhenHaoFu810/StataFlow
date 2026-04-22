# 棣栨寮€婧愬彲鐢ㄦ€ц川妫€鎶ュ憡

**鏃ユ湡锛?* 2026-04-19  
**瀹℃煡瑙掕壊锛?* Codex  
**瀹℃煡鐩爣锛?* 涓嶆柊澧炲姛鑳斤紝鍙瘎浼板綋鍓嶄粨搴撲綔涓衡€滅涓€娆″澶栧紑婧愮殑绗笁鏂瑰簱鈥濇槸鍚﹀凡缁忚揪鍒板彲鍙戝竷鐘舵€併€?
---

## 1. 瀹℃煡鑼冨洿

鏈璐ㄦ瑕嗙洊鍥涚被鍐呭锛?
1. **鏁板€间笌娴嬭瘯鍩虹嚎**
2. **绀轰緥涓庡熀鏈彲鐢ㄦ€?*
3. **瀵瑰鏂囨。涓庡叕鍏?API 璇箟**
4. **寮€婧愬彂甯冭浠讹紙鍏冩暟鎹€佽鍙瘉銆佷粨搴撴暣娲佸害銆佸彂甯冮潰涓€鑷存€э級**

鏈涓嶉噸鏂板瑁佲€滄槸鍚﹀畬鏁村鐜板叏閮?Stata 绀惧尯鍛戒护鈥濓紝鑰屾槸浠?*棣栨寮€婧愬彂甯冪殑璐ㄩ噺闂ㄦ**鍑哄彂璇勪及褰撳墠鐗堟湰鏄惁閫傚悎鍏紑缁欏閮ㄧ敤鎴蜂娇鐢ㄣ€?
---

## 2. 瀹為檯鎵ц鐨勬鏌?
### 2.1 娴嬭瘯鍩虹嚎

鎵ц锛?
```powershell
python -m pytest tests -v
```

缁撴灉锛?
- `687 passed`
- `0 failed`
- `2 warnings`

缁撹锛?
- 褰撳墠娴嬭瘯鍩虹嚎鏄?*寮轰笖绋冲畾**鐨勩€?- 鏍稿績浼拌鍣ㄣ€亀rapper銆乬olden dual-run銆乸ostestimation銆乫actor-variable銆丷D銆丏ID 璺緞閮借兘閫氳繃銆?
### 2.2 绀轰緥鑴氭湰鍙繍琛屾€?
鎵ц锛?
```powershell
python examples/demo_regress.py
python examples/demo_reghdfe.py
python examples/demo_ppmlhdfe.py
python examples/demo_ivregress_2sls.py
```

缁撴灉锛?
- 鍥涗釜 demo 鍧囨垚鍔熻繍琛屻€?- 杈撳嚭鏍煎紡鍙锛岄€傚悎浣滀负 README / examples 鍏ュ彛绀轰緥銆?
缁撹锛?
- 褰撳墠浠撳簱鑷冲皯宸茬粡鍏峰**鏈€灏忕殑鈥滄嬁鏉ュ氨璺戔€濅綋楠?*銆?
### 2.3 鏋勫缓鑳藉姏

鎵ц锛?
```powershell
python -m pip wheel . --no-deps -w .codex_tmp_dist
```

缁撴灉锛?
- wheel 鎴愬姛鏋勫缓锛歚stataflow-0.1.0-py3-none-any.whl`

缁撹锛?
- 褰撳墠浠撳簱**鍙互琚墦鍖?*锛屼笉鏄€滃彧鑳藉湪婧愮爜鐩綍閲岃窇鈥濈殑鍘熷瀷銆?
---

## 3. 鎬讳綋缁撹

### 3.1 鍙互鑲畾鐨勯儴鍒?
褰撳墠椤圭洰宸茬粡婊¤冻浠ヤ笅鏉′欢锛?
- 鏄竴涓?*楂樿川閲忋€佸己楠岃瘉**鐨?Alpha 鐗堟湰锛?- 涓昏鍛戒护鏃忛兘鏈?synthetic + real-data 鐨勫疄璇侀獙璇侀摼璺紱
- `compat.stata` 鍛戒护灞傚凡缁忓缓绔嬶紝涓嶅啀鍙槸搴曞眰 estimator 闆嗗悎锛?- 鏂囨。浣撶郴銆乻ource map銆乻upport matrix銆佸凡鐭ラ棶棰樼櫥璁伴兘姣旇緝瀹屾暣锛?- wheel 鑳芥瀯寤猴紝examples 鑳借窇锛宖ull test suite 绋冲畾銆?
### 3.2 涓嶈兘鐩存帴涓嬧€滃彲鏀惧績棣栨寮€婧愬彂甯冣€濈粨璁虹殑鍘熷洜

铏界劧绠楁硶鍜屾祴璇曢潰宸茬粡寰堝己锛屼絾浠?*绗竴娆″叕寮€寮€婧愬彂甯?*鐨勬爣鍑嗙湅锛屽綋鍓嶄粨搴撲粛鏈夊嚑椤规槑鏄剧煭鏉匡細

1. **缂哄皯 LICENSE 鏂囦欢**
2. **鎵撳寘鍏冩暟鎹笉瀹屾暣涓旈儴鍒嗕俊鎭笉涓€鑷?*
3. **瀵瑰鏂囨。涓粛鏈夐敊璇殑澶栭儴閾炬帴**
4. **浠撳簱鏍圭洰褰曚粛娣锋湁鍐呴儴鑴氭湰銆佽皟璇曡剼鏈拰鏃ュ織鏂囦欢**
5. **娌℃湁 CI/CD 宸ヤ綔娴?*

鍥犳锛屾湰娆℃渶缁堝垽鏂槸锛?
> **褰撳墠浠撳簱鍦ㄢ€滅畻娉曟纭€?+ 鏈湴鍙繍琛屾€р€濅笂宸茬粡杈惧埌楂樿川閲?Alpha 姘村钩锛屼絾鍦ㄢ€滈娆℃寮忓澶栧紑婧愨€濈殑鍙戝竷闈笂杩樻病鏈夊畬鍏ㄦ敹鍙ｃ€?*

鎹㈠彞璇濊锛?
- **浣滀负鍐呴儴 Alpha / 鐮旂┒鍨嬪叕寮€浠撳簱锛氬彲浠?*
- **浣滀负瀵瑰璁ょ湡瀹ｄ紶銆侀紦鍔遍檶鐢熺敤鎴风洿鎺ュ畨瑁呬娇鐢ㄧ殑棣栨寮€婧愮増鏈細杩樺樊鏈€鍚庝竴杞彂甯冮潰淇籍**

---

## 4. 涓昏鍙戠幇

### 4.1 Release-blocking

#### A. 缂哄皯 LICENSE 鏂囦欢

浠撳簱鏍圭洰褰曟病鏈?`LICENSE` / `COPYING` / `NOTICE` 鏂囦欢銆?
褰卞搷锛?
- 杩欎細璁╁閮ㄧ敤鎴峰拰璐＄尞鑰呮棤娉曟槑纭煡閬撲唬鐮佺殑浣跨敤銆佸垎鍙戝拰淇敼鏉冮檺銆?- 瀵光€滃紑婧愨€濇潵璇达紝杩欐槸鏈€鐩存帴銆佹渶鍩虹鐨勯樆濉炵偣銆?
鍒ゆ柇锛?
- **Release-blocking**

#### B. 鎵撳寘鍏冩暟鎹笉瀹屾暣涓斿瓨鍦ㄤ笉涓€鑷?
`pyproject.toml` 褰撳墠鍙湁鏈€灏忓瓧娈碉細

- `name`
- `version`
- `description`
- `requires-python`
- `dependencies`

浣嗙己灏戯細

- `readme`
- `license`
- `authors` / `maintainers`
- `keywords`
- `classifiers`
- `urls`

鍚屾椂杩樺瓨鍦ㄦ槑鏄句笉涓€鑷达細

- [README.md](/D:/OneDrive%20-%20SAIF/PhD3/StataFlow/README.md:34) 鍐欑殑鏄?`Python 3.9+`
- [pyproject.toml](/D:/OneDrive%20-%20SAIF/PhD3/StataFlow/pyproject.toml:9) 瀹為檯瑕佹眰鏄?`>=3.10`

褰卞搷锛?
- 鐢ㄦ埛浼氳鍒ゅ吋瀹圭幆澧冿紱
- PyPI / wheel 鍏冩暟鎹笉瀹屾暣锛屼笉鍒╀簬棣栨鍏紑鍙戝竷锛?- 鐗堟湰鎻忚堪鏄惧緱鏇村儚鍐呴儴鐮旂┒浠撳簱鑰屼笉鏄彲娑堣垂鐨勫寘銆?
鍒ゆ柇锛?
- **Release-blocking**

#### C. 瀵瑰 release 鏂囨。涓湁閿欒 issue 閾炬帴

[docs/release/open-source-alpha-status.md](/D:/OneDrive%20-%20SAIF/PhD3/StataFlow/docs/release/open-source-alpha-status.md:90) 褰撳墠鎶婂弽棣?issue 閾炬帴鎸囧悜浜?`anthropics/claude-code`銆?
褰卞搷锛?
- 澶栭儴鐢ㄦ埛浼氳瀵煎悜閿欒浠撳簱锛?- 浼氱洿鎺ユ崯瀹抽娆″紑婧愭椂鐨勫彲淇″害鍜屽熀鏈彲鐢ㄦ€с€?
鍒ゆ柇锛?
- **Release-blocking**

### 4.2 High priority

#### D. 浠撳簱鏍圭洰褰曞櫔闊虫枃浠惰繃澶?
鏍圭洰褰曞綋鍓嶄粛瀛樺湪澶氱鏄庢樉涓嶅簲浣滀负棣栨寮€婧愰椤垫毚闇茬殑鏂囦欢锛?
- `rdrobust_bwselect.log`
- `rdrobust_gen_z.log`
- `run_did_realdata_stata.py`
- `run_wagepan2.py`
- `run_wagepan3.py`
- `run_wagepan_check.py`
- `test_ezunem_didimp.py`
- `test_jtrain_didimp.py`
- `test_runner_simple.py`
- `find_mpdta.py`

褰卞搷锛?
- 澶栭儴鐢ㄦ埛浼氶毦浠ュ尯鍒嗭細
  - 姝ｅ紡 examples
  - 涓存椂璋冭瘯鑴氭湰
  - 涓€娆℃€х爺绌惰剼鏈?  - 鍐呴儴杈呭姪鑴氭湰
- 棣栨寮€婧愯鎰熶細鏄庢樉涓嬮檷銆?
鍒ゆ柇锛?
- **High priority**

#### E. 娌℃湁 CI/CD 宸ヤ綔娴?
浠撳簱涓病鏈?`.github/workflows/`銆?
褰卞搷锛?
- 澶栭儴璐＄尞鑰呮棤娉曠湅鍒拌嚜鍔ㄦ祴璇曠姸鎬侊紱
- 棣栨寮€婧愮己灏戞渶鍩虹鐨勨€滃彲楠岃瘉鎸佺画绋冲畾鈥濅俊鍙枫€?
鍒ゆ柇锛?
- **High priority**

### 4.3 Medium priority

#### F. 椤跺眰鍖呮枃妗堜粛淇濈暀鍘熷瀷鏈熺棔杩?
[src/stataflow/__init__.py](/D:/OneDrive%20-%20SAIF/PhD3/StataFlow/src/stataflow/__init__.py:1) 浠嶅啓鐫€锛?
- `# StataFlow - Phase 0 Bootstrap`

褰卞搷锛?
- 浼氬悜澶栭儴璇昏€呬紶杈锯€滈」鐩粛鏄?bootstrap 鍘熷瀷鈥濈殑閿欒淇″彿锛?- 涓庡綋鍓嶅凡缁忔墿灞曞埌 HDFE / IV / DID / RD 鐨勭姸鎬佷笉涓€鑷淬€?
鍒ゆ柇锛?
- **Medium priority**

#### G. 鍙戝竷涓庢不鐞嗘枃妗ｄ粛鏈夊巻鍙查仐鐣欐紓绉?
铏界劧 release-facing 鏂囨。鎬讳綋宸茬粡鏀跺彛锛屼絾鍐呴儴 `workspace/current-task/REPORT.md` 浠嶅瓨鍦ㄥ杞巻鍙?stale fresh-run 鏁板瓧鐨勫熬杩广€?
褰卞搷锛?
- 杩欎笉鏄閮ㄧ敤鎴风殑绗竴闃诲鐐癸紱
- 浣嗕細褰卞搷椤圭洰鍐呴儴璇佹嵁閾剧殑闀挎湡鍙俊搴︺€?
鍒ゆ柇锛?
- **Medium priority**

---

## 5. 棣栨寮€婧愬彂甯冨垽瀹?
### 鐜板湪鑳戒笉鑳藉紑婧愶紵

**鍙互鍏紑浠撳簱锛屼絾涓嶅缓璁湪褰撳墠鐘舵€佷笅鎶婂畠浣滀负鈥滄寮忓彲瀹夎銆佸彲娑堣垂鐨勯娆″紑婧愮増鏈€濆澶栧甯冦€?*

### 涓轰粈涔堬紵

鍥犱负褰撳墠闂涓嶅湪绠楁硶涓荤嚎锛岃€屽湪**鍙戝竷闈笌浠撳簱鍗敓**锛?
- 缂鸿鍙瘉
- 鍏冩暟鎹笉瀹屾暣
- README / release 鏂囨。閲岃繕鏈夐敊璇閾?- 鏍圭洰褰曡繃浜庢潅涔?
杩欎簺闂閮戒笉鏄€滀互鍚庡啀璇粹€濈殑灏忛棶棰橈紝鑰屾槸棣栨寮€婧愭椂鐢ㄦ埛绗竴鐪煎氨浼氱鍒扮殑闂銆?
### 杩樺樊澶氬皯锛?
涓嶅銆? 
浠庡綋鍓嶇姸鎬佸埌鈥滃彲浠ヨ鐪熷澶栧彂绗竴鐗?Alpha鈥濅箣闂达紝涓昏鏄?*涓€杞粨搴撴敹鍙ｅ拰鍙戝竷闈慨缂?*锛岃€屼笉鏄啀鑺卞緢澶氳疆鏀圭畻娉曘€?
