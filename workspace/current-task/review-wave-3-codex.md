# Wave 3 Codex Review

## 缁撹

鏈疆 **涓嶉€氳繃锛岄渶瑕佽繑宸?*銆?
闃诲鍘熷洜涓嶆槸娴嬭瘯濂椾欢娌¤繃锛岃€屾槸褰撳墠 `Binary / Count` 瀹炵幇涓瓨鍦ㄤ細绯荤粺鎬у奖鍝嶇粺璁℃帹鏂彛寰勭殑鏁板闂銆傜幇鏈?golden tests 涓昏瑕嗙洊浜嗙郴鏁般€佹爣鍑嗚鍜岄儴鍒嗘嫙鍚堢粺璁￠噺锛屼絾娌℃湁瑕嗙洊杩欎簺鎺ㄦ柇灞傚瓧娈碉紝鍥犳涓嶈兘鎹璁ゅ畾鏁翠釜 Wave 3 宸茶揪鎴?鈥淪tata 瀵归綈鈥濄€?
## 闃诲椤?
### 1. `logit` / `probit` / `poisson` 浣跨敤浜?`t` 鍒嗗竷鑰屼笉鏄?`z` 鍒嗗竷

- 鏂囦欢锛歚src/stataflow/estimators/glm.py`
- 璇佹嵁锛?  - 椤堕儴瀵煎叆 `t_dist`
  - `p_values = 2 * (1 - t_dist.cdf(...))`
  - `t_crit = t_dist.ppf(...)`
- 闂锛?  - Stata 鐨?`logit`銆乣probit`銆乣poisson` 灞炰簬 MLE 妗嗘灦锛岄粯璁ゆ姤鍛?**z-statistics** 涓庡熀浜庢爣鍑嗘鎬佸垎甯冪殑 p 鍊?缃俊鍖洪棿锛屼笉搴斾娇鐢?OLS 椋庢牸鐨?t 鍒嗗竷銆?  - 杩欎笉鏄樉绀哄眰宸紓锛岃€屾槸缁撴灉瀵硅薄鏈韩鐨勭粺璁″彛寰勯敊璇€傚嵆渚垮綋鍓?golden tests 娌¤鐩?`p_value` 鍜?`ci`锛屽叕寮€ API 宸茬粡鏆撮湶浜嗛敊璇帹鏂粨鏋溿€?- 澶勭悊瑕佹眰锛?  - 灏?MLE 璺緞鐨勬樉钁楁€ф楠屼笌缃俊鍖洪棿鏀逛负姝ｆ€佸垎甯冦€?  - 瀵?`logit`銆乣probit`銆乣poisson` 鍒嗗埆琛ヨ嚦灏戜竴缁勫瓧娈电骇娴嬭瘯锛屾槑纭牎楠?`p_value` / `ci_low` / `ci_high`銆?
### 2. `probit` 鐨?robust / cluster sandwich meat 鐢ㄩ敊浜?score

- 鏂囦欢锛歚src/stataflow/estimators/glm.py`
- 璇佹嵁锛?  - `Probit._compute_vce()` 涓?robust 鍒嗘敮浣跨敤 `residuals = y - mu`
  - cluster 鍒嗘敮浣跨敤 `score_g = X_g.T @ r_g`
- 闂锛?  - `probit` 涓嶆槸 canonical link銆傚叾瑙傛祴寰楀垎涓嶆槸绠€鍗曠殑 `x_i (y_i - p_i)`锛岃€屽簲涓猴細
    - `x_i * 蠁_i * (y_i - p_i) / (p_i * (1 - p_i))`
  - 鍥犳 robust 鍜?cluster 鐨?meat 涓嶈兘鐩存帴鐓ф惉 logit / poisson 鐨勬畫宸舰寮忋€?  - 鐜板湪 `vce="robust"` 鍜?`vce="cluster"` 铏界劧 API 鍙皟鐢紝浣嗘暟瀛︿笂涓嶆纭€傚摢鎬?Wave 3 鏈疆鍙妸 `vce="ols"` 浣滀负纭姹傦紝涔熶笉鑳借閿欒瀹炵幇缁х画鍏紑鏆撮湶銆?- 澶勭悊瑕佹眰锛?  - 鐢ㄦ纭殑 probit score 閲嶅啓 robust / cluster meat銆?  - 鑷冲皯鏂板涓€缁?probit robust 鎴?probit cluster 鐨?synthetic 瀵归綈鏍蜂緥锛岃瘉鏄庝慨姝ｅ悗鐨?VCE 鐪熸瀵归綈 Stata銆?  - 濡傛灉鏆傛椂涓嶅噯澶囧榻愶紝鍒欏簲鏄庣‘鍏抽棴璇ヨ矾寰勶紝鑰屼笉鏄繚鐣欓敊璇疄鐜般€?
### 3. `PPMLHDFE.fit(vce="ols")` 瀹為檯瀹炵幇鐨勬槸 robust sandwich锛屼笉鏄?conventional OIM/OLS

- 鏂囦欢锛歚src/stataflow/estimators/ppmlhdfe.py`
- 璇佹嵁锛?  - `if vce == "ols":` 鍒嗘敮涓嬫湁娉ㄩ噴锛歚ppmlhdfe always reports robust/sandwich SEs even without explicit vce option`
  - 鍒嗘敮涓娇鐢ㄤ簡 `meat = X' diag((y-mu)^2) X` 鐨?sandwich 褰㈠紡锛岃€屼笉鏄?conventional Hessian inverse
- 闂锛?  - 浠诲姟鍗″拰鍏紑鎺ュ彛閮芥妸杩欎竴鍒嗘敮鏆撮湶涓?`fit(vce="ols")`銆?  - 浣嗗疄鐜版湰璐ㄤ笂涓嶆槸 鈥淥LS/conventional鈥?鍙ｅ緞锛岃€屾槸绋冲仴鍙ｅ緞銆傝嫢 Stata 鍛戒护鏄惧紡鍐欎簡 `vce(ols)`锛屽垯杩欓噷鐨?Python 璇箟灏辨槸閿欒鏄犲皠銆?  - 濡傛灉浣犺涓诲紶 `ppmlhdfe` 榛樿搴斿綋鏄?robust锛岄偅涔熷簲璇ラ€氳繃 API 鍜岀粨鏋滃厓鏁版嵁鏄庣‘浣撶幇锛岃€屼笉鏄 `vce="ols"` 璧?robust銆?- 澶勭悊瑕佹眰锛?  - 浜岄€変竴锛?    1. 涓ユ牸瀹炵幇 `vce="ols"` 鐨?conventional VCE锛屽苟淇濇寔褰撳墠 API锛?    2. 閲嶆瀯 API / 鍛戒护鏄犲皠锛屾妸榛樿琛屼负涓?`vce="ols"` 璇箟鏄庣‘鍖哄垎銆?  - 鏃犺閲囩敤鍝鏂规锛岄兘闇€瑕佽ˉ娴嬭瘯璇佹槑 Stata 涓?Python 鐨?`vcetype` 鍜屾爣鍑嗚鍙ｅ緞涓€鑷淬€?
## 闈為樆濉炰絾闇€瑕佸叧娉?
### 4. Wave 3 鍥炴姤鎶?`ppmlhdfe` 鐨勯粯璁ょǔ鍋ユ帹鏂笌浠诲姟鍗¤姹傛贩鍦ㄤ竴璧?
- 褰撳墠鍥炴姤涓棦鍐欎簡 `fit(vce="ols")`锛屽張鍐欎簡 `ppmlhdfe` 榛樿 robust 鐨勫疄鐜伴€昏緫銆?- 杩欎細瀵艰嚧瀹℃煡鍙ｅ緞娣蜂贡锛氬埌搴曞綋鍓?wave 鏄湪瀵归綈 `vce(ols)`锛岃繕鏄湪瀵归綈鍛戒护榛樿鍊硷紵
- 杩斿伐鏃跺繀椤诲湪鍥炴姤涓妸杩欑偣璇存竻妤氾紝閬垮厤鍐嶇敤鈥滄祴璇曡繃浜嗏€濇帺鐩栫粺璁¤涔変笉涓€鑷淬€?
## 杩斿伐鍚庣殑鏈€浣庨噸鏂伴獙鏀惰姹?
鑷冲皯闇€瑕侀噸鏂版彁渚涗互涓嬭瘉鎹細

```bash
python -m pytest tests/golden/test_w3_logit_basic.py -v
python -m pytest tests/golden/test_w3_logit_real.py -v
python -m pytest tests/golden/test_w3_probit_basic.py -v
python -m pytest tests/golden/test_w3_probit_real.py -v
python -m pytest tests/golden/test_w3_poisson_basic.py -v
python -m pytest tests/golden/test_w3_poisson_real.py -v
python -m pytest tests/golden/test_w3_ppmlhdfe_basic.py -v
python -m pytest tests/golden/test_w3_ppmlhdfe_cluster.py -v
python -m pytest tests/golden/test_w3_ppmlhdfe_real_gravity.py -v
python -m pytest tests -v
```

姝ゅ蹇呴』鏂板鑷冲皯浠ヤ笅涓€绉嶏細

- `probit` 鐨?robust 鎴?cluster 榛勯噾娴嬭瘯
- `logit/probit/poisson` 鐨?`p_value` / `ci` 瀛楁娴嬭瘯
- `ppmlhdfe` 鐨?`vcetype` / VCE 璇箟娴嬭瘯

## 褰撳墠鐘舵€佸缓璁?
- 涓嶈鎺ㄨ繘鍒颁笅涓€ wave銆?- 鍏堟妸 Wave 3 杩斿伐鏀跺彛銆?- 鍙湁褰擄細
  - MLE 妯″瀷鐨勬帹鏂垎甯冩敼姝ｄ负 `z`
  - probit 鐨?sandwich score 淇瀹屾瘯
  - `ppmlhdfe` 鐨?`vce="ols"` 璇箟涓庡疄鐜颁竴鑷?  鎵嶈兘閲嶆柊杩涘叆瀹℃煡銆?