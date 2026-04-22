# Priority Wave Task 003锛歚reghdfe` 鐪熷疄鏁版嵁楠岃瘉涓庢敹鍙?
## 鍩烘湰淇℃伅

- 浠诲姟鍚嶇О锛歚reghdfe` 鐪熷疄鏁版嵁楠岃瘉涓庢敹鍙?- 鎵€灞炲懡浠ゆ棌锛歚Panel / FE / HDFE`
- 瀵瑰簲 backlog 鏉＄洰锛歚reghdfe`
- 浼樺厛绾э細P1
- 鎵ц浜猴細Claude Code
- 瀹℃煡浜猴細Codex

## 浠诲姟鐩爣

鏈疆鏄?`Priority Wave: reghdfe` 鐨?Round 3锛屼篃鏄浼樺厛娉㈡鐨勬敹鍙ｈ疆銆?
闇€瑕佷氦浠橈細

1. 瀹屾垚 `p3_reghdfe_real_panel` 鐨勭湡瀹炴暟鎹弻璺戙€?2. 浣跨敤鏈湴鍏紑鏁版嵁鑷冲皯瑕嗙洊涓€缁勭湡瀹為潰鏉挎牱渚嬶紝浼樺厛锛?   - `wagepan`
   - 濡傛湁蹇呰鍐嶈ˉ `Grunfeld`
3. 纭鐪熷疄鏁版嵁涓嬶細
   - 鏍锋湰绛涢€?   - singleton drop
   - 鑷姩 omitted 鐨?time-invariant / FE 鍏辩嚎鍙橀噺
   - 绯绘暟
   - 鏍囧噯璇?   - `df_a`
   - `df_resid`
   - `r2`
   - `rmse`
   - `f_stat`
   涓?Stata 涓€鑷淬€?4. 鑻ラ€氳繃锛屽垯鍥炲～ `docs/backlog.md` 鍜?`docs/testing/test-case-catalog.md`锛屽皢 `reghdfe` 姝ｅ紡鎺ㄨ繘涓?`done`銆?5. 鑻ラ€氳繃锛屽垯鍦ㄥ洖鎶ヤ腑鏄庣‘寤鸿缁撴潫 `Priority Wave: reghdfe`锛岃繘鍏ヤ笅涓€涓?wave銆?
## 蹇呰鏂囨。

1. `docs/operations/executor-playbook.md`
2. `docs/project-charter.md`
3. `docs/roadmap.md`
4. `docs/research/public-datasets.md`
5. `docs/research/reghdfe.md`
6. 鏈换鍔″崱

## 鏈疆鍏佽淇敼鐨勬枃浠?
- `tests/golden/` 涓?`p3_reghdfe_real_panel` 瀵瑰簲娴嬭瘯
- 蹇呰鐨勬祴璇曞伐鍏锋枃浠?- 鑻ョ湡瀹炴暟鎹毚闇叉渶灏忓疄鐜扮己闄凤紝鍙渶灏忎慨鏀癸細
  - `src/stataflow/estimators/absorbing_ols.py`
  - 濡傜‘鏈夊繀瑕侊紝鏈€灏忚寖鍥翠慨鏀?`src/stataflow/results/result.py`
- `docs/testing/test-case-catalog.md`
- `docs/backlog.md`
- `workspace/current-task/REPORT.md`

## 鏈疆绂佹浜嬮」

- 涓嶅緱瀹炵幇 `ivreghdfe`
- 涓嶅緱瀹炵幇 `ppmlhdfe`
- 涓嶅緱瀹炵幇 multi-way cluster
- 涓嶅緱鏂板鏂扮殑澶у姛鑳介潰
- 涓嶅緱鎶婄湡瀹炴暟鎹獙璇佸け璐ュ啓鎴愨€滃彲鎺ュ彈鈥濆悗鐩存帴鎺ㄨ繘 `done`

## 鐪熷疄鏁版嵁瑕佹眰

浼樺厛椤哄簭锛?
1. `wagepan`
2. `Grunfeld`

鏈疆鑷冲皯瀹屾垚涓€缁勭湡瀹炴暟鎹弻璺戯紱鑻ョ涓€缁勫凡瓒充互瑕嗙洊锛?
- 鍙屽悜 FE
- 鍗?cluster
- omitted 鍙橀噺
- `df_a` 宓屽鎵ｅ噺

鍒欎笉寮哄埗鍋氱浜岀粍銆?
鍥哄畾浣跨敤鏈湴鏁版嵁璺緞锛?
- `research/data/public/panel/wooldridge/wagepan.csv`
- `research/data/public/panel/grunfeld.csv`

## 娴嬭瘯瑕佹眰

### 蹇呭仛

- 鏂板鎴栬ˉ榻?`p3_reghdfe_real_panel`
- 鍏堣娴嬭瘯澶辫触
- 淇蹇呰鐨勬渶灏忛棶棰?- 璺戦€?`python -m pytest tests/golden/test_p3_reghdfe_real_panel.py -v`
- 鍐嶈窇 `python -m pytest tests -v`

### 蹇呴』姣斿鐨勫瓧娈?
- `nobs`
- `df_model`
- `df_a`
- `df_resid`
- `r2`
- `r2_adj`
- `rmse`
- `f_stat`
- 绯绘暟
- 鏍囧噯璇?- `cluster_count`
- `absorb_vars`

## 鍥炴姤瑕佹眰

鍥炴姤蹇呴』鑷冲皯鍖呭惈锛?
- 浣跨敤浜嗗摢涓€涓湡瀹炴暟鎹泦
- 鏁版嵁棰勫鐞嗕笌鏍锋湰绛涢€夎鏄?- singleton drop 涓?omitted 鍙橀噺璇存槑
- Stata 鍛戒护
- Python 璋冪敤
- 鎴愬姛瀵归綈鐨勫瓧娈?- 鑻ユ湁鍋忓樊锛屽亸宸瓧娈靛拰瑙ｉ噴
- 鏄惁寤鸿鎶?`reghdfe` 鏍囪涓?`done`
- 鏄惁寤鸿缁撴潫 `Priority Wave: reghdfe`

## 楠屾敹鏍囧噯

- `p3_reghdfe_real_panel` 閫氳繃
- `python -m pytest tests -v` 鍏ㄧ豢
- `docs/testing/test-case-catalog.md` 涓?`p3_reghdfe_real_panel` 鏇存柊涓?`done`
- `docs/backlog.md` 涓?`reghdfe` 鏇存柊涓?`done`
- 鏈疆鏈紩鍏?`ivreghdfe`銆乣ppmlhdfe` 鎴?multi-way cluster
- 鏃犳湭瑙ｉ噴缁熻鍋忓樊
