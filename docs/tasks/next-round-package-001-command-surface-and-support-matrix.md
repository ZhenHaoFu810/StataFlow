# 涓嬩竴杞换鍔″寘 001锛氬懡浠ゅ眰 API 涓庢敮鎸佺煩闃垫敹鍙?
## 鍩烘湰淇℃伅

- 浠诲姟鍚嶇О锛氬懡浠ゅ眰 API 涓庢敮鎸佺煩闃垫敹鍙?- 鎵€灞為樁娈碉細寮€婧愬垵鐗堜笅涓€杞?- 瀵瑰簲 backlog 鏉＄洰锛?  - `compat.stata` 鍛戒护灞?  - `regress`
  - `xtreg_fe`
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
- 浼樺厛绾э細P0
- 鎵ц浜猴細Claude Code
- 瀹℃煡浜猴細Codex

## 鐩爣

鏈换鍔″寘鐨勭洰鏍囦笉鏄墿寮犳柊鐨勮閲忓姛鑳斤紝鑰屾槸鎶婂綋鍓嶅凡缁忓瓨鍦ㄧ殑浼拌鍣ㄥ唴鏍稿彉鎴愪竴涓湡姝ｅ彲寮€婧愪娇鐢ㄧ殑 Stata 鍛戒护鏄犲皠灞傦紝骞跺缓绔嬫寮忕殑鏀寔鐭╅樀鏂囨。銆?
瀹屾垚鍚庡簲婊¤冻锛?
1. 鐢ㄦ埛鍙互閫氳繃 Stata 鍛戒护鍚嶈皟鐢ㄥ綋鍓嶅凡瀹炵幇鐨勯珮棰戝懡浠わ紝鑰屼笉蹇呯洿鎺ョ悊瑙ｅ唴閮ㄧ被鍚嶃€?2. 姣忎釜楂橀鍛戒护閮芥湁鐙珛鏀寔鐭╅樀锛屾槑纭€滃凡鏀寔 / planned / 鏄庣‘涓嶆敮鎸佲€濈殑鍙傛暟涓庤涓恒€?3. 瀵瑰鎺ュ彛涓嶅緱缁х画渚濊禆 `AbsorbingOLS`銆乣IVAbsorbingOLS` 杩欑鍐呴儴绫诲悕鏉ヨ〃杈惧懡浠よ涔夈€?4. 涓嶆敮鎸佺殑鍙傛暟蹇呴』纭姤閿欙紝涓嶅厑璁搁潤榛樺拷鐣ャ€?
## 蹇呰鏂囨。

1. `docs/operations/executor-playbook.md`
2. `docs/next-round-open-source-plan.md`
3. `docs/architecture/public-api.md`
4. `docs/architecture/overview.md`
5. `docs/backlog.md`
6. `docs/testing/test-case-catalog.md`
7. `docs/operations/codex-review-protocol.md`

## 鍓嶇疆鏉′欢

- [ ] 褰撳墠 wave 0-5 鐨勬棦鏈夋祴璇曚繚鎸佸彲杩愯
- [ ] 鏈换鍔″寘涓嶆搮鑷墿寮犳柊鐨勪及璁￠噺
- [ ] 鏈换鍔″寘涓嶆妸鈥滄帴鍙ｅ寘瑁呪€濅吉瑁呮垚鈥滃姛鑳藉畬鏁磋縼绉烩€?
## 鏈疆蹇呴』浜や粯

### A. 鏂板鍛戒护灞傜洰褰曚笌鍏ュ彛

鏂板鐩綍锛?
- `src/stataflow/compat/stata/`

鏈€浣庢枃浠讹細

- `src/stataflow/compat/__init__.py`
- `src/stataflow/compat/stata/__init__.py`
- `src/stataflow/compat/stata/linear.py`
- `src/stataflow/compat/stata/hdfe.py`
- `src/stataflow/compat/stata/iv.py`
- `src/stataflow/compat/stata/glm.py`
- `src/stataflow/compat/stata/did.py`

鏈€浣庡鍑哄嚱鏁帮細

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

### B. 鏂板鏀寔鐭╅樀鐩綍

鏂板鐩綍锛?
- `docs/command-support-matrix/`

鑷冲皯鍒涘缓浠ヤ笅鏂囦欢锛?
- `docs/command-support-matrix/regress.md`
- `docs/command-support-matrix/xtreg-fe.md`
- `docs/command-support-matrix/areg.md`
- `docs/command-support-matrix/reghdfe.md`
- `docs/command-support-matrix/ivregress-2sls.md`
- `docs/command-support-matrix/ivreghdfe.md`
- `docs/command-support-matrix/logit.md`
- `docs/command-support-matrix/probit.md`
- `docs/command-support-matrix/poisson.md`
- `docs/command-support-matrix/ppmlhdfe.md`
- `docs/command-support-matrix/did-imputation.md`
- `docs/command-support-matrix/eventstudyinteract.md`
- `docs/command-support-matrix/csdid.md`

姣忎唤鏀寔鐭╅樀鑷冲皯鍖呭惈锛?
- 鍛戒护鐩爣
- 褰撳墠 Python 鍏ュ彛
- 宸叉敮鎸佸弬鏁?- 宸叉敮鎸佺粨鏋滃瓧娈?- planned 鍙傛暟
- 鏄庣‘涓嶆敮鎸佸弬鏁?- 鐪熷疄瀵归綈璇佹嵁閾炬帴
- 瀵瑰簲鍐呮牳瀹炵幇鏂囦欢

### C. 鏀跺彛 README 涓庡叕寮€鍏ュ彛

蹇呴』鏇存柊锛?
- `README.md`
- `docs/architecture/public-api.md`
- `src/stataflow/__init__.py` 鎴栫瓑浠峰叕寮€鍏ュ彛

瑕佹眰锛?
- README 绀轰緥浼樺厛灞曠ず鍛戒护灞?API
- 淇濈暀 core estimator 绀轰緥锛屼絾涓嶅啀浣滀负鍞竴涓诲叆鍙?- 鏄庣‘鍖哄垎锛?  - core estimators
  - Stata compatibility commands

## 鏄庣‘涓嶅仛

鏈换鍔″寘涓嶈礋璐ｏ細

- 鏂颁及璁￠噺寮€鍙?- `reghdfe` / `ppmlhdfe` / `ivreghdfe` 鏁板灞傛柊澧炶兘鍔?- DID 鍛戒护鐨勬柊澧炰及璁℃柟娉?- `rdrobust` 瀹炵幇

濡傛灉鍦ㄥ寘瑁呰繃绋嬩腑鍙戠幇鏍稿績瀹炵幇鏃犳硶鏀拺 wrapper 璇箟锛屽彧鑳界櫥璁伴棶棰橈紝涓嶅緱椤烘墜鏃犺竟鐣屾墿绠楁硶銆?
## 鏍稿績鍘熷垯

### 1. 鍛戒护璇箟浼樺厛

瀵瑰 API 蹇呴』灏介噺閬靛畧 Stata 鍛戒护璇箟锛屽嵆浣垮唴閮ㄥ叡鐢ㄥ悓涓€鍐呮牳绫汇€?
### 2. 涓嶅緱闈欓粯蹇界暐鍙傛暟

鍑℃槸 wrapper 鏆撮湶鍑烘潵鐨勫弬鏁帮細

- 瑕佷箞瀹炵幇
- 瑕佷箞鏄惧紡鎶?`NotImplementedError` / `ValueError`

涓嶅緱鍑虹幇鈥滃弬鏁版敹杩涙潵浣嗘倓鎮勬病鐢熸晥鈥濄€?
### 3. 涓嶅緱浼€犲畬鏁存敮鎸?
鏀寔鐭╅樀蹇呴』璇氬疄鍙嶆槧褰撳墠瀹炵幇杈圭晫銆? 
濡傛灉 `reghdfe` 鍙敮鎸佸綋鍓嶅瓙闆嗭紝灏卞繀椤绘槑纭啓鎴愬瓙闆嗭紝鑰屼笉鏄啓鎴愨€滃凡瀹炵幇 reghdfe鈥濄€?
## 娴嬭瘯瑕佹眰

### 蹇呴』鏂板

鏂板鍛戒护灞?wrapper 娴嬭瘯锛岃嚦灏戣鐩栵細

- wrapper 鑳芥纭皟鐢ㄥ搴?estimator
- wrapper 鍙傛暟鑳芥纭槧灏勫埌 estimator
- 涓嶆敮鎸佸弬鏁颁細纭姤閿?- wrapper 缁撴灉瀵硅薄涓庡師 estimator 缁撴灉鏍稿績瀛楁涓€鑷?
寤鸿鏂板锛?
- `tests/test_compat_stata_linear.py`
- `tests/test_compat_stata_hdfe.py`
- `tests/test_compat_stata_iv.py`
- `tests/test_compat_stata_glm.py`
- `tests/test_compat_stata_did.py`

### 蹇呴』淇濈暀

- 鏃㈡湁 golden tests 鍏ㄩ儴閫氳繃
- 涓嶅緱閫氳繃鏀惧鐜版湁瀹瑰樊鏉ヨ wrapper 娴嬭瘯閫氳繃

## 楠屾敹鏍囧噯

- [ ] `src/stataflow/compat/stata/` 姝ｅ紡瀛樺湪
- [ ] 鎵€鏈夐珮棰戝懡浠ゅ凡鍏峰 wrapper
- [ ] wrapper 鐨勪笉鏀寔鍙傛暟浼氭樉寮忔姤閿?- [ ] 鏀寔鐭╅樀鏂囨。瀹屾暣
- [ ] README 涓庡叕寮€ API 鏂囨。鍚屾鏇存柊
- [ ] wrapper 娴嬭瘯閫氳繃
- [ ] 鍏ㄩ噺娴嬭瘯閫氳繃
- [ ] 鏃犫€滈潤榛樺拷鐣ュ弬鏁扳€濊涓?
## 鍥炴姤瑕佹眰

瀹屾垚鍚庡繀椤诲湪 `workspace/current-task/REPORT.md` 涓崟鐙垪鍑猴細

1. 鏂板浜嗗摢浜?wrapper
2. 姣忎釜 wrapper 鏆撮湶浜嗗摢浜涘弬鏁?3. 姣忎釜 wrapper 鏄惧紡鎷掔粷浜嗗摢浜涘弬鏁?4. 鏂板浜嗗摢浜涙敮鎸佺煩闃垫枃妗?5. 鏂板浜嗗摢浜?wrapper 娴嬭瘯
6. 鏄惁鍙戠幇褰撳墠 core 灞備笌鍛戒护璇箟鍐茬獊鐨勫湴鏂?