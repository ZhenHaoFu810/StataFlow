# Wave 1 Task 002锛歚areg` 鏈€灏忓疄鐜?
## 鍩烘湰淇℃伅

- 浠诲姟鍚嶇О锛歚areg` 鏈€灏忓疄鐜颁笌 synthetic 瀵归綈
- 鎵€灞炲懡浠ゆ棌锛歚Panel / FE / HDFE`
- 瀵瑰簲 backlog 鏉＄洰锛歚areg`
- 浼樺厛绾э細P1
- 鎵ц浜猴細Claude Code
- 瀹℃煡浜猴細Codex

## 浠诲姟鐩爣

鏈疆杩涘叆 Wave 1 鐨?Round 2锛屽彧鍋?`areg`锛屼笉纰?`reghdfe` 瀹炵幇銆?
闇€瑕佷氦浠橈細

1. 寮曞叆 `AbsorbingOLS` 鎴栫瓑浠锋渶灏忓唴鏍革紝鏀寔鍗曚竴鍚告敹鍙橀噺銆?2. 鎻愪緵 `areg` 鎵€闇€鐨勬渶灏忕粺璁¤涔夛細
   - 鍗曞惛鏀跺彉閲?   - `vce="ols"`
   - `_cons`
   - `df_a`
3. 璺戦€?`p3_areg_basic` synthetic 鍙岃窇銆?4. 鍏ㄩ噺娴嬭瘯涓嶅洖褰掋€?
## 蹇呰鏂囨。

1. `docs/operations/executor-playbook.md`
2. `docs/project-charter.md`
3. `docs/architecture/public-api.md`
4. `docs/architecture/stata-compatibility.md`
5. `docs/research/areg.md`
6. `docs/research/xtreg-fe.md`
7. 鏈换鍔″崱

## 鏈疆鍏佽淇敼鐨勬枃浠?
- `src/stataflow/estimators/` 涓嬩笌鍚告敹寮?OLS 鐩稿叧鐨勬渶灏忓疄鐜版枃浠?- `src/stataflow/__init__.py`
- `src/stataflow/estimators/__init__.py`
- `tests/golden/` 涓?`p3_areg_basic` 瀵瑰簲娴嬭瘯
- 濡傛湁蹇呰锛岃ˉ涓€涓渶灏忓崟鍏冩祴璇曟枃浠?- `docs/testing/test-case-catalog.md`
- `workspace/current-task/` 涓嬪洖鎶ユ枃浠?
## 鏈疆绂佹浜嬮」

- 涓嶅緱瀹炵幇 `reghdfe`
- 涓嶅緱瀹炵幇鍙屽悜 FE
- 涓嶅緱瀹炵幇 multi-way cluster
- 涓嶅緱鑷鎵╁睍鍒?`aweight + areg`
- 涓嶅緱鎶?`real_data` 楠岃瘉娣疯繘鏈疆锛涚湡瀹炴暟鎹暀鍒?Round 3

## 鏈€灏忓姛鑳借竟鐣?
鏈疆鍙壙璇猴細

- `AbsorbingOLS(data, y, x, absorb, add_constant=True, missing="drop")`
- `fit(vce="ols")`
- 鍗曚竴 `absorb` 鍙橀噺
- 缁撴灉瀵硅薄鑳借〃杈撅細
  - `df_a`
  - `fe_vars` 鎴栫瓑浠峰惛鏀跺厓鏁版嵁
  - `r2`
  - `rmse`
  - `f_stat`
  - 绯绘暟涓庡崗鏂瑰樊

## 娴嬭瘯瑕佹眰

### 蹇呭仛

- 鏂板 `p3_areg_basic` 榛勯噾娴嬭瘯
- 鍏堣鏂版祴璇曞け璐?- 鍐嶅疄鐜版渶灏忎唬鐮?- 鍐嶈璇ユ祴璇曢€氳繃
- 鏈€鍚庤窇 `pytest tests -v`

### 鏈疆涓嶅仛

- `p3_areg_real_panel`
- `p3_reghdfe_basic`
- `p3_reghdfe_real_panel`

## 鍥炴姤瑕佹眰

鍥炴姤蹇呴』鑷冲皯鍖呭惈锛?
- 淇敼鏂囦欢
- 鏂板娴嬭瘯
- `p3_areg_basic` 鐨?Stata 鍙岃窇缁撴灉
- `df_a`銆乣_cons`銆乣r2`銆乣rmse`銆乣f_stat` 鐨勫榻愭儏鍐?- 灏氬瓨椋庨櫓
- 鏄惁寤鸿寮€鏀?Round 3 鐨?`areg` 鐪熷疄鏁版嵁楠岃瘉

## 楠屾敹鏍囧噯

- `p3_areg_basic` 閫氳繃
- `pytest tests -v` 鍏ㄧ豢
- 鏈疆娌℃湁瑙︾ `reghdfe` 瀹炵幇
- `AbsorbingOLS` 鐨勬渶灏忔帴鍙ｄ笌鐮旂┒妗ｆ涓€鑷?- 鏃犳湭瑙ｉ噴缁熻鍋忓樊
