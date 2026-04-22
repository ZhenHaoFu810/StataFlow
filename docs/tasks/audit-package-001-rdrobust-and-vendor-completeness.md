# 瀹¤鍚庝换鍔″寘 001锛歚rdrobust` 鏈€灏忓彲楠岃瘉瀹炵幇 + Vendor 鍛戒护瀹屾暣搴︽敹鍙?
## 1. 浠诲姟瀹氫綅

杩欐槸瀹¤鍚庣殑绗竴寮犳柊浠诲姟鍗°€?
鐩爣涓嶆槸缁х画闆舵暎琛ュ姛鑳斤紝鑰屾槸鍚屾椂瀹屾垚涓や欢浜嬶細

1. 鎶?`rdrobust` 浠庘€滀粎鏈夋湰鍦版簮鐮侀暅鍍忋€佹棤 Python 瀹炵幇鈥濈殑鐘舵€侊紝鎺ㄨ繘鍒?*鏈€灏忓彲楠岃瘉瀹炵幇**銆?2. 鎶?`research/vendor/stata_community/` 涓?6 涓紑婧愬懡浠ょ殑**瀹屾暣搴︾姸鎬併€佹敮鎸佺煩闃点€乻ource map銆佹祴璇曡瘉鎹?*鍏ㄩ儴鏀跺彛鍒板彲渚?Codex 涓ユ牸瀹℃煡鐨勭姸鎬併€?
鏈疆鏄竴涓?*澶т换鍔″寘**銆傚厑璁告敼瀹炵幇銆佹祴璇曘€佹枃妗ｅ拰绀轰緥锛屼絾涓嶅厑璁告ā绯婅竟鐣屻€?
## 2. 鏈疆蹇呴』瀹屾垚鐨勫唴瀹?
### A. `rdrobust` 杩涘叆鐪熷疄瀹炵幇灞?
鑷冲皯瀹屾垚浠ヤ笅鍐呭锛?
- 鍦?`src/stataflow/estimators/` 涓柊澧?`rdrobust` 鐨勬牳蹇?estimator
- 鍦?`src/stataflow/compat/stata/` 涓柊澧?`rdrobust()` wrapper
- 鍦?`src/stataflow/__init__.py` 涓?`src/stataflow/compat/stata/__init__.py` 涓纭鍑?- 鍦?`docs/command-support-matrix/` 涓柊澧?`rdrobust.md`
- 鍦?`docs/research/` 涓柊澧炴垨琛ュ叏 `rdrobust-source-map.md`
- 鍦?`tests/` 涓柊澧?synthetic 娴嬭瘯涓庤嚦灏?1 涓?real-data / official-example 椋庢牸娴嬭瘯

### B. `rdrobust` 鐨勬渶灏忔敮鎸佽竟鐣屽繀椤绘槑纭?
鏈疆涓嶈姹傚畬鏁磋鐩?`rdrobust` 鐨勫叏閮ㄥ巻鍙查€夐」锛屼絾鏈€灏忓疄鐜板繀椤绘湁娓呮鐨勬暟瀛︿笌鍛戒护璇箟杈圭晫銆?
鏈€浣庤姹傦細

- sharp RD 涓昏矾寰?- 鏈湴澶氶」寮忓洖褰掓牳蹇冧及璁?- 鑷冲皯涓€绉?kernel
- 鑷冲皯涓€绉?bandwidth 閫夋嫨璺緞锛屾垨鏄庣‘瑕佹眰鐢ㄦ埛鏄惧紡浼犲甫瀹?- 涓?Stata 鍛戒护/婧愮爜涓€鑷寸殑鐐逛及璁″拰鍏抽敭鎺ㄦ柇瀵硅薄
- 缁撴灉瀵硅薄涓牳蹇冨瓧娈电殑绋冲畾璇箟

濡傛灉鏌愪簺鍏抽敭澶嶆潅鍔熻兘鏈疆涓嶅仛锛屼緥濡傦細

- fuzzy RD
- covariate-adjusted RD
- cluster VCE
- 瀹屾暣 bandwidth selector 瀹舵棌
- rdplot / rdbwselect 鍏ㄥ懡浠ら潰

蹇呴』锛?
- 鏄惧紡 hard-reject
- 鍐欏叆 support matrix
- 鍐欏叆 source map 鐨勨€滄湭瀹炵幇鈥濋儴鍒?- 鍦ㄦ姤鍛婇噷瑙ｉ噴涓轰粈涔堟病鍋?
### C. Vendor 鍏懡浠ゅ畬鏁村害鐭╅樀缁熶竴鏀跺彛

蹇呴』閲嶆柊鏍稿骞舵洿鏂颁互涓嬪懡浠ょ殑 support matrix 鍜?source map锛?
- `reghdfe`
- `ivreghdfe`
- `ppmlhdfe`
- `did_imputation`
- `eventstudyinteract`
- `rdrobust`

姣忎釜鍛戒护閮藉繀椤绘槑纭垎鎴愪笁绫伙細

- 宸插疄鐜板苟楠岃瘉
- 宸插疄鐜颁絾鍙槸瀛愰泦 / Phase A
- 鏈疄鐜版垨鏄惧紡鎷掔粷

涓嶅緱缁х画鍑虹幇鈥滃懡浠ゅ瓨鍦ㄢ€濅絾鈥滃畬鏁村害涓嶆竻妤氣€濈殑鍐欐硶銆?
### D. 娴嬭瘯涓庤瘉鎹摼鍗囩骇

鏈疆鏂板鐨勬祴璇曚笉鑳藉彧鏄€滀负浜嗚鏁板瓧杩団€濄€?
蹇呴』鍚屾椂鍖呭惈锛?
- synthetic / controlled case
- real-data 鎴栧畼鏂圭ず渚?case
- 鑷冲皯涓€涓洿鎺ラ拡瀵规暟瀛﹁繃绋嬬殑妫€鏌?
`rdrobust` 鑷冲皯闇€瑕侊細

- 1 涓?synthetic case锛氭鏌?cutoff 涓や晶灞€閮ㄥ椤瑰紡浼拌涓庢姤鍛婂瓧娈?- 1 涓?real-data / official-example case锛氫紭鍏堜娇鐢ㄦ湰鍦?`research/vendor/stata_community/rdrobust/` 涓彲澶嶇幇鏁版嵁鎴栫ず渚?
鍙﹀锛岄渶瑕佽嚦灏戣ˉ 1 涓€滃弽鍑戞暟鍊尖€濇祴璇曪紝渚嬪锛?
- 閿欒鍙傛暟蹇呴』鏄惧紡鎶ラ敊
- 鍏抽敭瀛楁涓嶈兘琚烦杩?- bandwidth / kernel / cutoff 鍙樺寲浼氬紩璧峰彲瑙ｉ噴鐨勭粨鏋滃彉鍖?
## 3. 鏁板涓庢簮鐮佸榻愯姹?
### A. 绂佹浜嬮」

浠ヤ笅浠讳竴鍋氭硶閮借涓烘湰杞け璐ワ細

- 閫氳繃璋冨瀹瑰樊璁?`rdrobust` 杩囨祴璇?- 鍙鍗曚竴鏍蜂緥鍙嶆帹鏁板€?- 鏃犳硶璇存槑浼拌閲忋€佸亸宸慨姝ｃ€佹爣鍑嗚鏉ヨ嚜婧愮爜鎴栨墜鍐屼綍澶?- wrapper 鏆撮湶浜嗗弬鏁帮紝浣嗗弬鏁板疄闄呬笂鏈敓鏁?
### B. 蹇呴』鍙В閲婄殑闂

浣犲湪瀹炵幇 `rdrobust` 鍚庯紝蹇呴』鑳藉湪鎶ュ憡涓槑纭洖绛旓細

- Python 瀹炵幇鐨勪及璁″璞℃槸浠€涔?- Stata 婧愮爜涓诲叆鍙ｆ槸鍝釜 `.ado` / `.do` / `.mata` / 鍏朵粬鏂囦欢
- 甯﹀銆乲ernel銆佸眬閮ㄥ椤瑰紡鏄浣曞搴斿埌 Python 瀹炵幇鐨?- 鎺ㄦ柇瀵硅薄鏄粈涔堬紝鏍囧噯璇浣曟瀯閫?- 鏈疆鍋氱殑鏄畬鏁?`rdrobust`锛岃繕鏄渶灏忓瓙闆嗭紱濡傛灉鏄瓙闆嗭紝缂虹殑鍏蜂綋鏄粈涔?
### C. 鑻ユ棤娉曞畬鏁磋В閲?
濡傛灉鍦ㄦ湰杞腑鍙戠幇 `rdrobust` 鏌愰儴鍒嗘病娉曞湪婧愮爜/鎵嬪唽涓婅娓呮锛屽垯锛?
- 鍙互淇濈暀鏈€灏忓疄鐜?- 浣嗗繀椤绘妸鏈В閲婇儴鍒嗗垪涓烘湭瀹屾垚
- 涓嶈兘鍥犱负娴嬭瘯杩囦簡灏卞绉扳€滃畬鏁村疄鐜扳€?
## 4. 鍏佽淇敼鐨勮寖鍥?
鏈疆鍏佽淇敼锛?
- `src/stataflow/estimators/`
- `src/stataflow/compat/stata/`
- `src/stataflow/__init__.py`
- `src/stataflow/compat/stata/__init__.py`
- `tests/`
- `docs/command-support-matrix/`
- `docs/research/`
- `docs/testing/test-case-catalog.md`
- `docs/backlog.md`
- `README.md`锛堝闇€鏂板 `rdrobust` 鍛戒护璇存槑锛?- `workspace/current-task/REPORT.md`

## 5. 涓嶅厑璁镐慨鏀圭殑鑼冨洿

鏈疆涓嶈鎿呰嚜淇敼锛?
- `docs/project-charter.md`
- `docs/architecture/public-api.md` 鐨勯《灞傚師鍒?- `docs/operations/codex-review-protocol.md`

闄ら潪浣犲彂鐜拌繖浜涙枃妗ｄ笌鏈疆瀹炵幇鐩存帴鐭涚浘锛屽苟鍦ㄦ姤鍛婁腑鏄庣‘璇存槑鍘熷洜銆?
## 6. 楠岃瘉瑕佹眰

鏈疆鑷冲皯鎵ц骞跺洖鎶ヤ互涓嬮獙璇侊細

### 鍏ㄩ噺鍩虹嚎

```powershell
python -m pytest tests -v
```

### `rdrobust` 涓撻」

浣犳柊澧炵殑 `rdrobust` 娴嬭瘯鏂囦欢蹇呴』鍗曠嫭 fresh run銆?
### Vendor 鐩稿叧涓撻」

鑷冲皯閲嶆柊璺戜竴缁勪笌 vendor 鍛戒护鐩稿叧鐨勪笓椤规祴璇曪紝纭繚鏈疆鏀瑰姩娌℃湁鐮村潖宸叉湁鍛戒护锛?
- `tests/test_hdfe_synthetic.py`
- `tests/test_compat_stata_did.py`
- 鑷冲皯涓€缁?`reghdfe` / `ppmlhdfe` / `did_imputation` golden tests

### 杩愯鏃舵娊鏌?
鑷冲皯瀹為檯璋冪敤涓€娆★細

- `stataflow.compat.stata.rdrobust(...)`
- 涓€涓凡鏈?vendor wrapper锛屼緥濡?`reghdfe(...)` 鎴?`ppmlhdfe(...)`

纭繚 wrapper 璇箟銆佽繑鍥炲璞″拰鏂囨。涓€鑷淬€?
## 7. 瀹屾垚鏍囧噯

鏈疆瑕佽瑙嗕负閫氳繃锛岃嚦灏戦渶瑕佹弧瓒筹細

1. `rdrobust` 宸茬粡涓嶅啀鏄?鈥渕issing鈥?2. `rdrobust` 鏈夌湡瀹?Python 瀹炵幇銆亀rapper銆乻upport matrix銆乻ource map銆佹祴璇?3. 鍏釜 vendor 鍛戒护鐨勫畬鏁村害鐘舵€佸叏閮ㄦ竻妤?4. support matrix / source map / tests / report 涓嶄簰鐩告墦鏋?5. 娌℃湁鍙戠幇鈥滀负浜嗚繃娴嬭瘯鑰屽噾鏁板€尖€濈殑璇佹嵁

## 8. 鎶ュ憡鏍煎紡瑕佹眰

鍦?[workspace/current-task/REPORT.md](</D:/OneDrive - SAIF/PhD3/StataFlow/workspace/current-task/REPORT.md>) 涓寜浠ヤ笅缁撴瀯鍥炴姤锛?
### 1. 鏈疆鏀瑰姩姒傝

### 2. `rdrobust` 瀹炵幇璇存槑

- 浼拌瀵硅薄
- 婧愮爜鍏ュ彛
- 鏈疆鏀寔鍙傛暟
- 鏈疆鏄庣‘涓嶆敮鎸佸弬鏁?
### 3. Vendor 鍏懡浠ゅ畬鏁村害鏇存柊琛?
蹇呴』閫愪釜鍐欙細

- `reghdfe`
- `ivreghdfe`
- `ppmlhdfe`
- `did_imputation`
- `eventstudyinteract`
- `rdrobust`

### 4. 楠岃瘉缁撴灉

- 鍏ㄩ噺娴嬭瘯
- `rdrobust` 涓撻」
- 鍏朵粬涓撻」

### 5. 宸茬煡鍓╀綑闂

### 6. 璇锋眰 Codex 閲嶇偣瀹℃煡鐨勯棶棰?
濡傛灉浣犱笉纭畾鏌愬鏄惁杈惧埌浜嗏€滄暟瀛﹁繃绋嬪榻愨€濈殑鏍囧噯锛屽繀椤荤偣鍚嶈鎴戦噸鐐瑰銆?
