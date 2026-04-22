# Priority Wave Task 002锛歚reghdfe` 鏈€灏忓疄鐜?
## 鍩烘湰淇℃伅

- 浠诲姟鍚嶇О锛歚reghdfe` 鏈€灏忓疄鐜颁笌 synthetic 瀵归綈
- 鎵€灞炲懡浠ゆ棌锛歚Panel / FE / HDFE`
- 瀵瑰簲 backlog 鏉＄洰锛歚reghdfe`
- 浼樺厛绾э細P1
- 鎵ц浜猴細Claude Code
- 瀹℃煡浜猴細Codex

## 浠诲姟鐩爣

鏈疆鏄?`Priority Wave: reghdfe` 鐨?Round 2锛屽彧鍋?`Phase A` 鐨勬渶灏忓疄鐜帮紝涓嶅仛鐪熷疄鏁版嵁鏀跺彛銆?
闇€瑕佷氦浠橈細

1. 鍦ㄧ幇鏈?`AbsorbingOLS` 鍩虹涓婃敮鎸?`absorb=[var1]` 涓?`absorb=[var1, var2]`銆?2. 鏀寔 `reghdfe Phase A` 鐨勬渶灏忕粺璁¤涔夛細
   - 1-2 涓垎绫?FE
   - `vce="ols"`
   - 鍗?`vce="cluster"`
   - 榛樿 singleton drop
   - `df_a`銆乣df_r`銆乣cluster_count`
3. 璺戦€氫互涓?synthetic 榛勯噾鏍蜂緥锛?   - `p3_reghdfe_basic`
   - `p3_reghdfe_cluster`
4. 鑻ラ渶瑕佹柊澧?`p3_reghdfe_two_fe` 浣滀负绾弻 FE OLS synthetic 鏍蜂緥锛屽彲鍦ㄦ湰杞ˉ鐧昏骞跺疄鐜般€?5. 鍏ㄩ噺娴嬭瘯涓嶅洖褰掋€?
## 蹇呰鏂囨。

1. `docs/operations/executor-playbook.md`
2. `docs/project-charter.md`
3. `docs/architecture/public-api.md`
4. `docs/architecture/stata-compatibility.md`
5. `docs/research/reghdfe.md`
6. `docs/research/stata-source-inventory.md`
7. 鏈换鍔″崱

## 鏈疆鍏佽淇敼鐨勬枃浠?
- `src/stataflow/estimators/absorbing_ols.py`
- `src/stataflow/estimators/__init__.py`
- 濡傜‘鏈夊繀瑕侊紝鏈€灏忚寖鍥翠慨鏀?`src/stataflow/results/result.py`
- `tests/golden/` 涓?`reghdfe` 瀵瑰簲 synthetic 娴嬭瘯
- 蹇呰鐨勬祴璇曞伐鍏锋枃浠?- `docs/testing/test-case-catalog.md`
- `workspace/current-task/REPORT.md`

## 鏈疆绂佹浜嬮」

- 涓嶅緱鍋?`reghdfe` 鐨勭湡瀹炴暟鎹弻璺戞敹鍙?- 涓嶅緱瀹炵幇 `ivreghdfe`
- 涓嶅緱瀹炵幇 `ppmlhdfe`
- 涓嶅緱瀹炵幇 multi-way cluster
- 涓嶅緱鎶婃湭鐮旂┒娓呮鐨?mobility group / pairwise DoF 淇纭杩?Phase A
- 涓嶅緱鎶婄湡瀹炴暟鎹け璐ユ垨鏈獙璇佸瓧娈靛啓鎴愨€滃彲鎺ュ彈鈥濆悗鐩存帴鎺ㄨ繘

## 鏈€灏忓姛鑳借竟鐣?
鏈疆鍙壙璇猴細

- `AbsorbingOLS(..., absorb=[var1])`
- `AbsorbingOLS(..., absorb=[var1, var2])`
- `fit(vce="ols")`
- `fit(vce="cluster", cluster="...")`
- 榛樿鑷姩 drop singleton 瑙傛祴
- 缁撴灉瀵硅薄鑳借〃杈撅細
  - `df_a`
  - `df_r`
  - `cluster_count`
  - `absorb_vars`
  - `r2`
  - `rmse`
  - `f_stat`
  - 绯绘暟涓庡崗鏂瑰樊

## 娴嬭瘯瑕佹眰

### 蹇呭仛

- 鏂板鎴栬ˉ榻?`p3_reghdfe_basic`
- 鏂板鎴栬ˉ榻?`p3_reghdfe_cluster`
- 濡傚紩鍏?`p3_reghdfe_two_fe`锛屽繀椤诲厛鍦ㄦ牱渚嬬洰褰曠櫥璁?- 鍏堣鏂版祴璇曞け璐?- 鍐嶅疄鐜版渶灏忎唬鐮?- 璺戦€氬搴?synthetic 榛勯噾娴嬭瘯
- 鏈€鍚庤窇 `python -m pytest tests -v`

### 鏈疆涓嶅仛

- `p3_reghdfe_real_panel`
- 浠讳綍鐪熷疄鏁版嵁鏀跺彛
- `robust` 濡傛棤娉曠ǔ瀹氬榻愬彲鍏堜笉寮€鏀撅紝浣嗕笉寰椾吉瑁呬负宸叉敮鎸?
## 蹇呴』姣斿鐨勫瓧娈?
- `nobs`
- `df_model`
- `df_a`
- `df_resid`
- `r2`
- `rmse`
- `f_stat`
- 绯绘暟
- 鏍囧噯璇?- `cluster_count`锛坈luster 鏃讹級
- `absorb_vars`

## 鍥炴姤瑕佹眰

鍥炴姤蹇呴』鑷冲皯鍖呭惈锛?
- 淇敼鏂囦欢
- 鏂板鎴栨洿鏂扮殑 synthetic 娴嬭瘯
- `p3_reghdfe_basic` 鐨?Stata 鍙岃窇缁撴灉
- `p3_reghdfe_cluster` 鐨?Stata 鍙岃窇缁撴灉
- singleton drop銆乣df_a`銆乣df_r`銆乣F`銆乧luster 淇鐨勫榻愭儏鍐?- 灏氬瓨椋庨櫓
- 鏄惁寤鸿寮€鏀?`Priority Wave Task 003 - reghdfe real-data validation`

## 楠屾敹鏍囧噯

- `p3_reghdfe_basic` 閫氳繃
- `p3_reghdfe_cluster` 閫氳繃
- `python -m pytest tests -v` 鍏ㄧ豢
- 鏈疆鏈Е纰扮湡瀹炴暟鎹敹鍙?- 鏈疆鏈墿灞曞埌 `ivreghdfe` 鎴?`ppmlhdfe`
- 鏃犳湭瑙ｉ噴鐨勫叧閿粺璁″亸宸?