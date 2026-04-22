# Priority Wave Task 001锛歚reghdfe` 鐮旂┒鏀舵潫涓庡疄鐜拌竟鐣岀‘璁?
## 鍩烘湰淇℃伅

- 浠诲姟鍚嶇О锛歚reghdfe` 鐮旂┒鏀舵潫涓庡疄鐜拌竟鐣岀‘璁?- 鎵€灞炲懡浠ゆ棌锛歚Panel / FE / HDFE`
- 瀵瑰簲 backlog 鏉＄洰锛歚reghdfe`
- 浼樺厛绾э細P1
- 鎵ц浜猴細Claude Code
- 瀹℃煡浜猴細Codex

## 浠诲姟鐩爣

鏈疆鏄?`Priority Wave: reghdfe` 鐨?Round 1锛屽彧鍋氱爺绌舵敹鏉燂紝涓嶅仛瀹炵幇銆?
闇€瑕佷氦浠橈細

1. 灏嗙幇鏈?`reghdfe` 鐮旂┒妗ｆ鏀舵潫涓哄彲鐩存帴杩涘叆鏈€灏忓疄鐜扮殑瑙勬牸璇存槑銆?2. 鍩轰簬鏈湴婧愮爜闀滃儚锛屾槑纭細
   - 鏈€灏忓疄鐜扮殑 `ado` / `mata` 鍏ュ彛
   - 闇€瑕佷紭鍏堟ā浠跨殑绠楁硶璺緞
   - 鏆備笉鏀寔鐨勯€夐」闈?3. 灏?`reghdfe Phase A` 鐨勬渶灏忓吋瀹瑰瓙闆嗗啓娓呮锛?   - `absorb()` 鏀寔 1-2 缁?FE
   - `vce(ols)`
   - 鍗?`cluster`
   - singleton 榛樿 drop 鐨勫彛寰?   - `df_a`銆乣df_r`銆乣F` 鐨勯噸鐐瑰榻愬瓧娈?4. 妫€鏌ュ苟琛ラ綈 `synthetic` 涓?`real_data` 鏍蜂緥璁捐锛屼娇鍏惰冻浠ユ敮鎾戜笅涓€杞渶灏忓疄鐜般€?5. 褰㈡垚涓€浠界粨鏋勫寲鐮旂┒鍥炴姤锛屾槑纭槸鍚﹀彲浠ュ紑鏀?`reghdfe` 鏈€灏忓疄鐜般€?
## 蹇呰鏂囨。

1. `docs/operations/executor-playbook.md`
2. `docs/project-charter.md`
3. `docs/roadmap.md`
4. `docs/roadmap-execution-rounds.md`
5. `docs/research/reghdfe.md`
6. `docs/research/stata-source-inventory.md`
7. `docs/research/public-datasets.md`
8. 鏈换鍔″崱

## 鏈疆鍏佽淇敼鐨勬枃浠?
- `docs/research/reghdfe.md`
- `docs/research/stata-source-inventory.md`
- `docs/testing/test-case-catalog.md`
- `workspace/current-task/REPORT.md`

濡傜‘鏈夊繀瑕侊紝鍙柊澧烇細

- `docs/research/reghdfe-phase-a-notes.md`

## 鏈疆绂佹浜嬮」

- 涓嶅緱淇敼 `src/stataflow/` 涓嬩换浣曞疄鐜颁唬鐮?- 涓嶅緱鏂板 `reghdfe` 鐨?Python API 瀹炵幇
- 涓嶅緱椤哄娍鎵╁睍鍒?`ivreghdfe`銆乣ppmlhdfe` 鎴栧鍚?cluster
- 涓嶅緱鎶婄爺绌剁粨璁虹洿鎺ュ啓鎴愨€滃凡瀹屾垚瀹炵幇鈥?- 涓嶅緱鎶婃湭楠岃瘉鐨勭粺璁″樊寮傛彁鍓嶈瀹氫负鈥滃彲鎺ュ彈鈥?
## 闇€瑕佸畬鎴愮殑鐮旂┒鍐呭

### A. 鏈湴婧愮爜鍏ュ彛鏀舵潫

鑷冲皯鏄庣‘锛?
- `reghdfe.ado` 鐨勪富鍛戒护鍏ュ彛
- 鍏抽敭 `mata` 鏂囦欢涓庤亴璐ｅ垝鍒?- 鍝潯绠楁硶璺緞鏈€閫傚悎浣滀负 Python `Phase A` 鐨勬渶灏忓弬鑰冨疄鐜?- 鏄惁渚濊禆 `ftools` 鐨勭壒瀹氳涓猴紝鑻ヤ緷璧栵紝濡備綍鍦?Python 涓娊璞℃浛浠?
### B. `Phase A` 鏈€灏忓疄鐜拌竟鐣?
鑷冲皯鍐欐竻锛?
- 鏀寔鍝簺 `absorb()` 褰㈡€?- 鍗?`cluster` 鐨勬渶灏忚涔?- singleton 澶勭悊鍙ｅ緞
- `df_a`銆乣df_r`銆乣N_clust`銆乣F` 鐨勯獙鏀跺瓧娈?- `_cons`銆佺郴鏁板懡鍚嶃€佺粨鏋滃璞″厓鏁版嵁濡備綍琛ㄨ揪

### C. 娴嬭瘯璁捐鏀舵潫

鑷冲皯纭鎴栬ˉ榻愶細

- `p3_reghdfe_basic`
- `p3_reghdfe_cluster`
- `p3_reghdfe_real_panel`

姣忎釜鏍蜂緥閮借鍐欐槑锛?
- 浣跨敤鍝粍鏁版嵁
- Stata 鍛戒护
- 棰勬湡 Python API
- 涓昏椋庨櫓鐐?- 鏈疆涔嬪悗鏄?`ready` 杩樻槸浠嶅簲 `planned`

## 鍥炴姤瑕佹眰

鍥炴姤蹇呴』鑷冲皯鍖呭惈锛?
- 淇敼鏂囦欢娓呭崟
- `reghdfe Phase A` 鐨勬槑纭姛鑳借竟鐣?- 鏈湴婧愮爜鍏ュ彛涓庝紭鍏堝弬鑰冭矾寰?- 寤鸿鐨勬渶灏忔祴璇曠煩闃?- 灏氭湭瑙ｅ喅鐨勭粺璁￠闄?- 鏄惁寤鸿寮€鏀?`Priority Wave Task 002 - reghdfe 鏈€灏忓疄鐜癭

## 楠屾敹鏍囧噯

- `docs/research/reghdfe.md` 宸茶兘鐩存帴鏀拺瀹炵幇杞?- 鏈湴婧愮爜鍏ュ彛銆佷緷璧栧拰绠楁硶浼樺厛璺緞宸叉槑纭?- `docs/testing/test-case-catalog.md` 涓?`reghdfe` 鏍蜂緥鐧昏瀹屾暣涓旂姸鎬佸悎鐞?- 鏈疆鏈Е纰颁换浣曞疄鐜颁唬鐮?- 鍥炴姤涓棤鈥滅爺绌朵唬鏇垮疄鐜板畬鎴愨€濈殑琛ㄨ堪
