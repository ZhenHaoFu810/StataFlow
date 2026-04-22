# Wave 1 Task 001锛欻DFE 鐮旂┒鍩虹寤鸿

## 鍩烘湰淇℃伅

- 浠诲姟鍚嶇О锛歚areg` / `reghdfe` 鐮旂┒鍩虹寤鸿
- 鎵€灞炲懡浠ゆ棌锛歚Panel / FE / HDFE`
- 瀵瑰簲 backlog 鏉＄洰锛歚areg`銆乣reghdfe`
- 浼樺厛绾э細P1
- 鎵ц浜猴細Claude Code
- 瀹℃煡浜猴細Codex

## 浠诲姟鐩爣

鏈疆鍙仛鐮旂┒涓庤璁★紝涓嶅仛瀹炵幇銆?
闇€瑕佷氦浠橈細

1. 鎶?`docs/research/areg.md` 琛ユ垚鍙墽琛岀爺绌舵。妗堛€?2. 鎶?`docs/research/reghdfe.md` 琛ユ垚鍙墽琛岀爺绌舵。妗堛€?3. 鍒╃敤鏈湴婧愮爜闀滃儚锛屽畾浣?`reghdfe` 鐨勬牳蹇?`ado` / `mata` 鍏ュ彛銆佷緷璧栦笌鍏抽敭閫夐」銆?4. 涓?`areg` 鍜?`reghdfe` 鍒嗗埆璁捐锛?   - synthetic 榛勯噾鏍蜂緥
   - real-data 鏍蜂緥
5. 灏嗗搴旀牱渚嬮鐧昏鍒?`docs/testing/test-case-catalog.md`銆?6. 褰㈡垚涓€浠界粨鏋勫寲鐮旂┒鍥炴姤锛屼緵 Codex 鍐冲畾涓嬩竴杞槸鍚﹀紑鏀惧疄鐜颁换鍔°€?
## 蹇呰鏂囨。

1. `docs/operations/executor-playbook.md`
2. `docs/project-charter.md`
3. `docs/roadmap.md`
4. `docs/research/stata-source-inventory.md`
5. `docs/research/public-datasets.md`
6. `docs/research/areg.md`
7. `docs/research/reghdfe.md`

## 鏈疆鍏佽淇敼鐨勬枃浠?
- `docs/research/areg.md`
- `docs/research/reghdfe.md`
- `docs/research/stata-source-inventory.md`
- `docs/testing/test-case-catalog.md`
- `workspace/current-task/` 涓嬬殑鍥炴姤鏂囦欢

濡傜‘鏈夊繀瑕侊紝鍙柊澧烇細

- `docs/research/hdfe-notes.md`

## 鏈疆绂佹浜嬮」

- 涓嶅緱淇敼 `src/stataflow/` 涓嬩换浣曞疄鐜颁唬鐮?- 涓嶅緱鏂板 `docs/tasks/` 涓殑瀹炵幇鍨嬩换鍔″崱
- 涓嶅緱鏀瑰姩椤圭洰绔犵▼銆佸叕鍏?API 鍘熷垯鍜岀粺璁＄瓑浠风粨璁?- 涓嶅緱鎶娾€滈槄璇绘簮鐮佸緱鍒板垵姝ョ悊瑙ｂ€濈洿鎺ュ啓鎴愨€滃凡瀹屾垚瀹炵幇鈥?
## 闇€瑕佸畬鎴愮殑鐮旂┒鍐呭

### A. `areg`

鑷冲皯琛ラ綈锛?
- 鍛戒护鐢ㄩ€斾笌鍏稿瀷鐮旂┒鍦烘櫙
- 涓?`xtreg, fe` 鐨勫叧绯讳笌宸紓
- 鍏抽敭杩斿洖鍊?- 鑷敱搴︿笌鏁翠綋妫€楠岀粺璁￠噺闇€瑕侀噸鐐规瘮瀵圭殑瀛楁
- synthetic 鏍蜂緥璁捐
- real-data 鏍蜂緥璁捐
- 鏈€灏忓疄鐜板瓙闆嗗缓璁?
### B. `reghdfe`

鑷冲皯琛ラ綈锛?
- 鏈湴闀滃儚鐩綍涓殑鏍稿績婧愮爜鍏ュ彛
- 渚濊禆鐨勫叾浠栧懡浠ゆ垨妯″潡
- 鍏抽敭閫夐」锛?  - `absorb()`
  - `vce(robust)`
  - `vce(cluster)`
  - singleton 澶勭悊
  - DoF 淇
- 杈撳嚭瀛楁涓庡簲閲嶇偣姣斿鐨?`e()` 缁撴灉
- synthetic 鏍蜂緥璁捐
- real-data 鏍蜂緥璁捐
- 鏈€灏忓吋瀹瑰瓙闆嗗缓璁?
## 鏍蜂緥鐧昏瑕佹眰

鍦?`docs/testing/test-case-catalog.md` 涓嚦灏戦鐧昏浠ヤ笅鏉＄洰锛?
- `p3_areg_basic`
- `p3_areg_real_panel`
- `p3_reghdfe_basic`
- `p3_reghdfe_real_panel`

杩欎簺鏉＄洰褰撳墠鐘舵€佸簲涓?`ready`锛屼笉鏄?`done`銆?
## 寤鸿浣跨敤鐨勭湡瀹炴暟鎹?
- `areg`
  - `wagepan`
  - `Grunfeld`
- `reghdfe`
  - 鍏堢敤鏈湴 `wagepan` 鎴?`Grunfeld` 璁捐鏈€灏忕湡瀹炴牱渚?  - 濡傛灉闇€瑕佹洿閫傚悎鐨勯珮缁?FE 鏁版嵁锛屽湪鍥炴姤涓彁鍑哄€欓€夛紝浣嗘湰杞笉寮哄埗涓嬭浇鏇村鏁版嵁

## 鍥炴姤瑕佹眰

鍥炴姤蹇呴』鑷冲皯鍖呭惈锛?
- 淇敼鏂囦欢娓呭崟
- `areg` 鐮旂┒缁撹鎽樿
- `reghdfe` 鐮旂┒缁撹鎽樿
- `reghdfe` 鏈湴婧愮爜鍏ュ彛璺緞
- 寤鸿鐨勬渶灏忓疄鐜板瓙闆?- 棰勭櫥璁版牱渚嬫竻鍗?- 鏄惁寤鸿涓嬩竴杞紑鏀惧疄鐜颁换鍔?
## 楠屾敹鏍囧噯

- `docs/research/areg.md` 宸蹭粠鍗犱綅鍗囩骇涓哄彲鎵ц鐮旂┒妗ｆ
- `docs/research/reghdfe.md` 宸蹭粠鍗犱綅鍗囩骇涓哄彲鎵ц鐮旂┒妗ｆ
- `docs/testing/test-case-catalog.md` 宸茬櫥璁?`areg` / `reghdfe` 鐨?synthetic 鍜?real-data 鏉＄洰
- 鍥炴姤涓槑纭啓鍑?`reghdfe` 鐨勬湰鍦版簮鐮佸叆鍙ｄ笌渚濊禆
- 鏈疆娌℃湁瑙︾浠讳綍瀹炵幇浠ｇ爜
