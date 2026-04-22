# Wave 1 Task 003锛歚areg` 鐪熷疄鏁版嵁楠岃瘉涓庢敹鍙?
## 鍩烘湰淇℃伅

- 浠诲姟鍚嶇О锛歚areg` 鐪熷疄鏁版嵁楠岃瘉涓庢敹鍙?- 鎵€灞炲懡浠ゆ棌锛歚Panel / FE / HDFE`
- 瀵瑰簲 backlog 鏉＄洰锛歚areg`
- 浼樺厛绾э細P1
- 鎵ц浜猴細Claude Code
- 瀹℃煡浜猴細Codex

## 浠诲姟鐩爣

鏈疆鏄?Wave 1 鐨?Round 3锛屽彧鍋?`areg` 鐨勭湡瀹炴暟鎹弻璺戜笌鏀跺彛锛屼笉鍐嶆墿灞曟柊鍔熻兘銆?
闇€瑕佷氦浠橈細

1. 瀹屾垚 `p3_areg_real_panel` 鐨勭湡瀹炴暟鎹弻璺戙€?2. 浣跨敤鏈湴鍏紑鏁版嵁鑷冲皯瑕嗙洊涓€缁勭湡瀹為潰鏉挎牱渚嬶紝浼樺厛锛?   - `wagepan`
   - `Grunfeld`
3. 纭鐪熷疄鏁版嵁涓嬶細
   - 鏍锋湰绛涢€?   - 缂哄け鍊煎鐞?   - 绯绘暟
   - 鏍囧噯璇?   - `df_a`
   - `r2`
   - `rmse`
   - `f_stat`
   涓?Stata 涓€鑷淬€?4. 鑻ラ€氳繃锛屽垯鍥炲～ `docs/backlog.md` 鍜?`docs/testing/test-case-catalog.md`锛屽皢 `areg` 姝ｅ紡鎺ㄨ繘涓?`done`銆?
## 蹇呰鏂囨。

1. `docs/operations/executor-playbook.md`
2. `docs/project-charter.md`
3. `docs/research/public-datasets.md`
4. `docs/research/areg.md`
5. `docs/research/xtreg-fe.md`
6. 鏈换鍔″崱

## 鏈疆鍏佽淇敼鐨勬枃浠?
- `tests/golden/` 涓?`p3_areg_real_panel` 瀵瑰簲娴嬭瘯
- 蹇呰鐨勬祴璇曞伐鍏锋枃浠?- `docs/testing/test-case-catalog.md`
- `docs/backlog.md`
- `workspace/current-task/` 涓嬪洖鎶ユ枃浠?
鑻ョ湡瀹炴暟鎹獙璇佹毚闇茶交寰疄鐜扮己闄凤紝鍙渶灏忎慨鏀癸細

- `src/stataflow/estimators/absorbing_ols.py`

浣嗕笉寰楅『鍔挎墿灞曟柊鍔熻兘闈€?
## 鏈疆绂佹浜嬮」

- 涓嶅緱瀹炵幇 `reghdfe`
- 涓嶅緱鎺ㄨ繘鍙屽悜 FE
- 涓嶅緱鏂板 `areg` 鐨?`robust` / `cluster` / `aweight` 鏀寔
- 涓嶅緱鏂板绗簩涓湡瀹炴暟鎹懡浠ゆ棌浠诲姟
- 涓嶅緱鎶婄湡瀹炴暟鎹獙璇佸け璐ュ啓鎴愨€滃彲鎺ュ彈鈥濆悗鐩存帴鎺ㄨ繘 `done`

## 鐪熷疄鏁版嵁瑕佹眰

浼樺厛椤哄簭锛?
1. `wagepan`
2. `Grunfeld`

鏈疆鑷冲皯瀹屾垚涓€缁勭湡瀹炴暟鎹弻璺戯紱濡傛灉涓ょ粍閮借兘瀹屾垚鏇村ソ锛屼絾涓嶆槸纭姹傘€?
Stata 鑴氭湰鍜?Python 娴嬭瘯閮藉繀椤诲浐瀹氫娇鐢ㄦ湰鍦版暟鎹矾寰勶細

- `research/data/public/panel/wooldridge/wagepan.csv`
- `research/data/public/panel/grunfeld.csv`

## 娴嬭瘯瑕佹眰

### 蹇呭仛

- 鏂板 `p3_areg_real_panel` 榛勯噾娴嬭瘯
- 鍏堣娴嬭瘯澶辫触
- 淇蹇呰鐨勬渶灏忛棶棰?- 璺戦€?`pytest tests/golden/test_p3_areg_real_panel.py -v`
- 鍐嶈窇 `pytest tests -v`

### 蹇呴』姣斿鐨勫瓧娈?
- `nobs`
- `df_model`
- `df_a`
- `df_resid`
- `r2`
- `rmse`
- `f_stat`
- 绯绘暟
- 鏍囧噯璇?
## 鍥炴姤瑕佹眰

鍥炴姤蹇呴』鑷冲皯鍖呭惈锛?
- 浣跨敤浜嗗摢涓€涓湡瀹炴暟鎹泦
- 鏁版嵁棰勫鐞嗕笌鏍锋湰绛涢€夎鏄?- Stata 鍛戒护
- Python 璋冪敤
- 鎴愬姛瀵归綈鐨勫瓧娈?- 鑻ユ湁鍋忓樊锛屽亸宸瓧娈靛拰瑙ｉ噴
- 鏄惁寤鸿鎶?`areg` 鏍囪涓?`done`

## 楠屾敹鏍囧噯

- `p3_areg_real_panel` 閫氳繃
- `pytest tests -v` 鍏ㄧ豢
- `docs/testing/test-case-catalog.md` 涓?`p3_areg_real_panel` 鏇存柊涓?`done`
- `docs/backlog.md` 涓?`areg` 鏇存柊涓?`done`
- 鏈疆鏈紩鍏?`reghdfe` 鎴栧弻鍚?FE 鐨勫疄鐜?