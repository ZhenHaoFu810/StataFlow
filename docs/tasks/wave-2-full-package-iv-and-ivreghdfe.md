# Wave 2 Full Package锛歚IV / GMM` 鏁村寘浠诲姟

## 鍩烘湰淇℃伅

- 浠诲姟鍚嶇О锛歐ave 2 鍏ㄥ寘鎺ㄨ繘锛歚ivregress 2sls` + `ivreghdfe` 鏈€灏忛棴鐜?- 鎵€灞炲懡浠ゆ棌锛歚IV / GMM`
- 瀵瑰簲 backlog 鏉＄洰锛?  - `ivregress 2sls`
  - `ivreghdfe`
- 浼樺厛绾э細P2
- 鎵ц浜猴細Claude Code
- 瀹℃煡浜猴細Codex

## 浠诲姟鐩爣

杩欐槸涓€涓?*鏁村寘 wave 浠诲姟**銆侰laude Code 闇€瑕佸湪涓€涓繛缁换鍔′腑瀹屾垚 Wave 2 鐨勭爺绌躲€佹渶灏忓疄鐜板拰鐪熷疄鏁版嵁楠岃瘉锛屼絾蹇呴』鎸夋湰浠诲姟鍗″唴閮ㄧ殑闃舵闂ㄧ鎺ㄨ繘锛屼笉鑳借烦姝ャ€?
鏈€缁堢洰鏍囷細

1. 瀹屾垚 `ivregress 2sls` 鐨勭爺绌躲€佹渶灏忓疄鐜般€乻ynthetic 瀵归綈鍜岀湡瀹炴暟鎹榻愩€?2. 瀹屾垚 `ivreghdfe` 鐨勭爺绌舵敹鏉熴€佹渶灏忓疄鐜般€乻ynthetic 瀵归綈鍜岀湡瀹炴暟鎹榻愩€?3. 鑻ュ叏閮ㄩ€氳繃锛屽垯灏?Wave 2 瀵瑰簲鏉＄洰鏍囪涓?`done`锛屽苟鍦ㄥ洖鎶ヤ腑鏄庣‘寤鸿杩涘叆涓嬩竴 wave銆?
## 蹇呰鏂囨。

1. `docs/operations/executor-playbook.md`
2. `docs/project-charter.md`
3. `docs/architecture/public-api.md`
4. `docs/architecture/stata-compatibility.md`
5. `docs/roadmap.md`
6. `docs/roadmap-execution-rounds.md`
7. `docs/research/stata-source-inventory.md`
8. `docs/research/public-datasets.md`
9. `docs/research/ivreghdfe.md`
10. 鏈换鍔″崱

## 鎬讳綋鑼冨洿

### 蹇呭仛

- `ivregress 2sls`
- `ivreghdfe`
- synthetic 榛勯噾鏍蜂緥
- 鑷冲皯涓€缁勭湡瀹炲叕寮€鏁版嵁鏍蜂緥

### 涓嶅仛

- `liml`
- `gmm`
- 杩囧害璇嗗埆/寮卞伐鍏风殑瀹屾暣宸ュ叿閾?- multi-way cluster
- `ppmlhdfe`
- 鏂扮殑 DID 鍛戒护

## 鎵ц鍘熷垯

鏈换鍔¤櫧鐒舵槸涓€鏁村寘锛屼絾浠嶅繀椤绘寜涓変釜鍐呴儴闃舵鎺ㄨ繘锛?
1. `Stage A: Research closure`
2. `Stage B: Minimum implementation + synthetic`
3. `Stage C: Real-data validation + hardening`

浠讳綍涓€涓樁娈垫湭閫氳繃锛屼笉寰楀湪鍥炴姤涓啓鎴愭暣涓?Wave 2 瀹屾垚銆?
## Stage A锛歊esearch closure

### 闇€瑕佸畬鎴?
1. 灏?`docs/research/ivreghdfe.md` 浠庡崰浣嶆枃妗ｈˉ鎴愬彲鎵ц鐮旂┒妗ｆ銆?2. 鏂板鎴栬ˉ榻?`docs/research/ivregress-2sls.md`銆?3. 鍦?`docs/testing/test-case-catalog.md` 棰勭櫥璁颁互涓嬫牱渚嬶細
   - `w2_ivregress_basic`
   - `w2_ivregress_cluster`
   - `w2_ivregress_real_card`
   - `w2_ivreghdfe_basic`
   - `w2_ivreghdfe_cluster`
   - `w2_ivreghdfe_real_panel`
4. 鏄庣‘锛?   - `ivregress 2sls` 鐨勭粨鏋滃瓧娈点€佺涓€闃舵涓庣浜岄樁娈电粺璁″彛寰?   - `ivreghdfe` 涓?`reghdfe` / `ivreg2` 鐨勪緷璧栧叧绯?   - 鏈€灏忓吋瀹瑰瓙闆?   - 鏆備笉鏀寔鐨勯€夐」闈?
### 鐮旂┒缁撹蹇呴』鍥炵瓟

- 2SLS 鐐逛及璁′笌鍗忔柟宸殑瀹炵幇璺緞鏄粈涔?- `vce(robust)` 鍜屽崟 `cluster` 鏄惁绾冲叆鏈?wave 鐨勬渶灏忓疄鐜?- `ivreghdfe` 濡備綍澶嶇敤鐜版湁 `AbsorbingOLS` / `reghdfe` 鍩虹
- 鐪熷疄鏁版嵁鏍蜂緥浣跨敤鍝竴缁勬暟鎹?
## Stage B锛歁inimum implementation + synthetic

### `ivregress 2sls`

鑷冲皯瀹炵幇锛?
- `IV2SLS(data, y, x_exog, x_endog, instruments, add_constant=True)`
- `fit(vce="ols")`
- `fit(vce="cluster", cluster="...")`
- 缁撴灉瀵硅薄鑷冲皯琛ㄨ揪锛?  - `nobs`
  - `df_model`
  - `df_resid`
  - `r2`
  - `rmse`
  - `f_stat`
  - 绯绘暟涓庡崗鏂瑰樊

### `ivreghdfe`

鑷冲皯瀹炵幇锛?
- 鍦?HDFE 鍩虹涓婃敮鎸佹渶灏?2SLS 璺緞
- `absorb` 鏀寔 1-2 涓?FE
- `fit(vce="ols")`
- 鍗?`cluster`
- 榛樿 singleton drop 鍙ｅ緞寤剁画 `reghdfe`

### synthetic 蹇呭仛鏍蜂緥

- `w2_ivregress_basic`
- `w2_ivregress_cluster`
- `w2_ivreghdfe_basic`
- `w2_ivreghdfe_cluster`

## Stage C锛歊eal-data validation + hardening

### `ivregress 2sls` 鐪熷疄鏁版嵁

鑷冲皯瀹屾垚涓€缁勫叕寮€鐪熷疄鏁版嵁鏍蜂緥銆備紭鍏堝€欓€夛細

- `Card` returns-to-schooling 鏁版嵁
- 鍏朵粬鍏紑鍙鐜扮殑鏁欏 IV 鏁版嵁

鑻ユ湰鍦颁笉瀛樺湪锛屽彲涓嬭浇鍒帮細

- `research/data/public/iv/`

骞惰ˉ鏁版嵁鏂囨。銆?
### `ivreghdfe` 鐪熷疄鏁版嵁

鑷冲皯瀹屾垚涓€缁勫叕寮€鐪熷疄 panel 鏁版嵁鏍蜂緥銆備紭鍏堝€欓€夛細

- `wagepan`

鍏佽涓轰簡璁＄畻楠岃瘉鑰屾瀯閫犳淳鐢熷彉閲忥紙濡傛粸鍚庡伐鍏枫€佸鐢熷伐鍏峰彉閲忥級锛屼絾蹇呴』鍦ㄥ洖鎶ヤ腑鏄庣‘锛?
- 娲剧敓瑙勫垯
- Stata 涓?Python 浣跨敤瀹屽叏鐩稿悓鐨勬牱鏈笌鍙橀噺瀹氫箟
- 杩欓噷鐨勭洰鐨勫彧鏄獙璇佹暟鍊煎疄鐜帮紝涓嶅璇嗗埆鏈夋晥鎬т綔棰濆鎵胯

### 蹇呴』姣斿瀛楁

- `nobs`
- `df_model`
- `df_resid`
- `r2`
- `rmse`
- `f_stat`
- 绯绘暟
- 鏍囧噯璇?- `cluster_count`锛坈luster 鏃讹級
- `absorb_vars`锛坄ivreghdfe` 鏃讹級

## 鍏佽淇敼鐨勬枃浠?
- `src/stataflow/estimators/` 涓?IV / HDFE 鐩稿叧鏈€灏忓疄鐜?- `src/stataflow/results/result.py`
- `src/stataflow/__init__.py`
- `src/stataflow/estimators/__init__.py`
- `tests/golden/` 涓?Wave 2 瀵瑰簲娴嬭瘯
- 蹇呰鐨勬祴璇曞伐鍏锋枃浠?- `docs/research/` 涓嬪搴旂爺绌舵。妗?- `docs/testing/test-case-catalog.md`
- `docs/backlog.md`
- `docs/research/public-datasets.md`
- `workspace/current-task/REPORT.md`

## 绂佹浜嬮」

- 涓嶅緱鎶婃湭瀹屾垚鐨勫瓙闃舵鍐欐垚鏁翠釜 Wave 2 瀹屾垚
- 涓嶅緱鎶婄湡瀹炴暟鎹け璐ュ啓鎴愨€滃彲鎺ュ彈鈥濈洿鎺ユ斁琛?- 涓嶅緱椤哄娍鎵╁睍鍒?`liml`銆乣gmm`銆佸鍚?cluster銆乣ppmlhdfe`
- 涓嶅緱淇敼椤圭洰绔犵▼鎴栧叕鍏?API 鍘熷垯

## 寮哄埗楠岃瘉鍛戒护

鑷冲皯蹇呴』杩愯骞跺湪鍥炴姤涓粰鍑虹粨鏋滐細

```bash
python -m pytest tests/golden/test_w2_ivregress_basic.py -v
python -m pytest tests/golden/test_w2_ivregress_cluster.py -v
python -m pytest tests/golden/test_w2_ivregress_real_card.py -v
python -m pytest tests/golden/test_w2_ivreghdfe_basic.py -v
python -m pytest tests/golden/test_w2_ivreghdfe_cluster.py -v
python -m pytest tests/golden/test_w2_ivreghdfe_real_panel.py -v
python -m pytest tests -v
```

鑻ユ渶缁堥噰鐢ㄤ笉鍚屾祴璇曟枃浠跺悕锛岄渶鍦ㄥ洖鎶ヤ腑瑙ｉ噴骞剁粰鍑哄疄闄呭懡浠ゃ€?
## 鍥炴姤瑕佹眰

鍥炴姤蹇呴』鍒嗕笁娈靛啓锛?
1. `Stage A`
   - 鐮旂┒妗ｆ鏀瑰姩
   - 鏁版嵁涓庢牱渚嬬櫥璁?   - 鏈€灏忓疄鐜拌竟鐣?2. `Stage B`
   - 瀹炵幇鏂囦欢
   - synthetic 瀵归綈缁撴灉
   - 灏氬瓨缁熻椋庨櫓
3. `Stage C`
   - 鐪熷疄鏁版嵁鏉ユ簮
   - 鏁版嵁棰勫鐞嗕笌宸ュ叿鍙橀噺瀹氫箟
   - Stata 鍛戒护
   - Python 璋冪敤
   - 瀵归綈瀛楁
   - Wave 2 鏄惁鍙爣璁颁负瀹屾垚

## Wave 2 閫氳繃鏍囧噯

鍙湁鍚屾椂婊¤冻浠ヤ笅鏉′欢锛孋odex 鎵嶄細璁ゅ畾鏁翠釜 Wave 2 瀹屾垚锛?
- `ivregress 2sls` synthetic + real-data 鍏ㄩ€氳繃
- `ivreghdfe` synthetic + real-data 鍏ㄩ€氳繃
- 鍏ㄩ噺鍥炲綊娴嬭瘯閫氳繃
- `docs/backlog.md` 涓?`docs/testing/test-case-catalog.md` 鐘舵€佷竴鑷?- 鏃犳湭瑙ｉ噴鐨勫叧閿粺璁″亸宸?
鑻ヤ换涓€椤逛笉婊¤冻锛孋odex 灏嗗彧璁ゅ畾宸插畬鎴愮殑瀛愰樁娈碉紝涓嶄細鏀捐鏁翠釜 wave銆?