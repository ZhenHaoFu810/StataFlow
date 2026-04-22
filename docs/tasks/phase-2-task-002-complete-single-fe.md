# Phase 2 Task 002锛氭帹杩涘畬鎴?Single FE 闃舵浜や粯

## 鍩烘湰淇℃伅

- 浠诲姟鍚嶇О锛歋ingle FE 涓?FE + cluster 鑱斿悎浜や粯
- 鎵€灞為樁娈碉細Phase 2
- 瀵瑰簲 backlog 鏉＄洰锛歚鍗曞悜 FE`銆乣鍗曞悜 FE + vce(cluster)`
- 浼樺厛绾э細P2
- 鎵ц浜猴細QwenCode
- 瀹℃煡浜猴細Codex

## 鐩爣

鍦ㄦ湰杞唴灏介噺鎺ㄨ繘瀹屾垚 Phase 2 鍓╀綑鏍稿績鑼冨洿锛?
1. 浜や粯 `FixedEffectsOLS` 鎴栫瓑浠峰叕寮€鎺ュ彛锛屾敮鎸佸崟涓€ FE 鍙橀噺銆?2. 瀹屾垚 `xtreg ..., fe` 涓?Python 瀹炵幇鐨?Stata 鍙岃窇瀵圭収銆?3. 瀹屾垚 `xtreg ..., fe vce(cluster firm_id)` 涓?Python 瀹炵幇鐨?Stata 鍙岃窇瀵圭収銆?4. 灏?Phase 2 backlog銆佹牱渚嬬洰褰曞拰宸ヤ綔鍖哄叆鍙ｆ洿鏂板埌鍙鏌ョ姸鎬併€?
鏈疆鍏佽宸ヤ綔閲忔槑鏄惧ぇ浜庡墠鍑犺疆锛屼絾浠嶉渶鍧氭寔鈥滃厛娴嬪悗鍐欌€濆拰 Stata 瀵归綈浼樺厛銆?
## 蹇呰鏂囨。

鎸変互涓嬮『搴忛槄璇伙紝涓嶈璺虫锛?
1. `docs/operations/qwencode-playbook.md`
2. `docs/operations/review-gates.md`
3. `docs/phases/phase-2-weights-fe.md`
4. `docs/architecture/public-api.md`
5. `docs/architecture/result-schema.md`
6. `docs/architecture/stata-compatibility.md`
7. 鏈换鍔″崱 `docs/tasks/phase-2-task-002-complete-single-fe.md`

## 鍓嶇疆鏉′欢

- [ ] 宸茬‘璁?`Phase 2 Task 001 - aweight` 宸茬敱 Codex 楠屾敹閫氳繃
- [ ] 宸插湪 `docs/testing/test-case-catalog.md` 涓櫥璁?`p2_fe_basic` 涓?`p2_fe_cluster`
- [ ] 宸茬‘璁ゆ湰杞笉鎵╁睍鍒板弻鍚?FE銆侀珮缁?FE銆乣areg` 鎴栨柊鏉冮噸绫诲瀷

## 鏈疆鎵ц姝ラ

1. 鍏堣ˉ娴嬭瘯涓庢牱渚嬭璁?   - 涓?`p2_fe_basic` 璁捐闈㈡澘鏍蜂緥涓庨粍閲戞祴璇曘€?   - 涓?`p2_fe_cluster` 璁捐闈㈡澘鏍蜂緥涓庨粍閲戞祴璇曘€?   - 鏄庣‘ Stata 渚у懡浠ゃ€佽緭鍑哄瓧娈靛拰瀹瑰樊銆?2. 鍏堣繍琛屾祴璇曞苟閿佸畾澶辫触鐐?   - 鏂版祴璇曞厛搴斿け璐ワ紝璇佹槑褰撳墠瀹炵幇灏氭湭婊¤冻銆?3. 瀹炴柦鏈€灏忓叕寮€鎺ュ彛
   - 鏂板 `FixedEffectsOLS` 鎴栧湪鐜版湁妯″潡鍐呰ˉ鍏呯瓑浠风被銆?   - 瀵瑰鎺ュ彛蹇呴』鏄庣‘ `fe=` 鍙傛暟鍜?`fit(vce=...)` 褰㈡€併€?   - 缁撴灉瀵硅薄瀛楁蹇呴』涓?OLS 璺緞鍏煎銆?4. 瀹炴柦鍗曞悜 FE 涓昏矾寰?   - 瀹炵幇鍗曚釜 FE 鍙橀噺鐨?within 鍙樻崲鎴栫瓑浠锋畫宸寲銆?   - 鏄庣‘ `nobs`銆乣df_model`銆乣df_resid`銆乣r2`銆乣rmse`銆乣f_stat` 鐨?Stata 瀵归綈鍙ｅ緞銆?   - 灏?FE 鍏冩暟鎹啓鍏ョ粨鏋滃璞★紝渚嬪 `fe_vars`銆?5. 瀹炴柦 FE + cluster
   - 鍦ㄥ崟鍚?FE 鍩虹涓婃敮鎸?`vce="cluster"`銆?   - 鏄庣‘ cluster 涓暟銆佽嚜鐢卞害淇銆佹暣浣撴楠岀粺璁￠噺涓?Stata 鐨勫搴旀柟寮忋€?6. 璺戝畬鏁撮獙璇?   - 杩愯鏂板 FE 榛勯噾娴嬭瘯銆?   - 杩愯 `pytest tests -v`锛屼笉寰楀紩鍏ュ洖褰掋€?7. 鍥炲～鏂囨。涓庤瘉鎹?   - 濡傞€氳繃锛屽皢 `docs/backlog.md` 涓?`鍗曞悜 FE` 涓?`鍗曞悜 FE + vce(cluster)` 鏇存柊涓?`done`銆?   - 灏?`docs/testing/test-case-catalog.md` 涓?`p2_fe_basic`銆乣p2_fe_cluster` 鏇存柊涓?`done`銆?   - 鐢?`workspace/qwencode-current/REPORT_TEMPLATE.md` 鎻愪氦瀹屾垚鎶ュ憡銆?
## 闇€瑕佹柊澧炴垨淇敼鐨勬枃浠?
- 浠ｇ爜锛?  - `src/stataflow/estimators/` 涓嬩笌 FE 鐩稿叧鐨勫疄鐜版枃浠?  - 濡傞渶鍏紑瀵煎嚭锛屾洿鏂?`src/stataflow/__init__.py` 鎴栫浉搴旀ā鍧楀叆鍙?- 娴嬭瘯锛?  - `tests/golden/test_p2_fe_basic.py`
  - `tests/golden/test_p2_fe_cluster.py`
- 鏂囨。锛?  - `docs/backlog.md`
  - `docs/testing/test-case-catalog.md`
  - 蹇呰鏃惰ˉ鍏?FE 鐩稿叧璇存槑锛屼絾涓嶅緱鏀瑰啓椤跺眰鍘熷垯

## 楠屾敹鏍囧噯

- [ ] `p2_fe_basic` 鍙岃窇閫氳繃
- [ ] `p2_fe_cluster` 鍙岃窇閫氳繃
- [ ] `pytest tests -v` 鍏ㄧ豢
- [ ] FE 璺緞缁撴灉瀵硅薄涓?OLS 璺緞鍏煎
- [ ] `f_stat` 涓?Stata 瀵归綈锛屼笉鎺ュ彈鈥滅粺璁￠噺绫诲瀷涓嶅悓浣嗗彲鎺ュ彈鈥濈殑璇存槑
- [ ] 鏂囨。鐘舵€佷笌瀹屾垚鎶ュ憡涓€鑷?- [ ] 鏃犳湭瑙ｉ噴鍋忓樊

## 绂佹浜嬮」

- 涓嶅緱鎵╁睍鍒板弻鍚?FE銆侀珮缁?FE銆乣areg`
- 涓嶅緱鎶?`robust + FE` 浣滀负鏈疆闅愬惈鑼冨洿
- 涓嶅緱璺宠繃 Stata 鍙岃窇锛屼粎浠?Python 鑷祴鏇夸唬
- 涓嶅緱鎶?Stata 涓?Python 鍦ㄦ暣浣撴楠岀粺璁￠噺涓婄殑宸紓璁颁负鈥滃彲鎺ュ彈鈥濆悗鐩存帴鏀捐
- 涓嶅緱淇敼椤圭洰绔犵▼銆丄DR 鎴栫粺璁＄瓑浠峰師鍒欐潵瑙勯伩瀹炵幇闅剧偣

## 椋庨櫓涓庡娉?
- 鑻?`xtreg, fe` 鐨勬煇浜涚粺璁￠噺涓庣洿鎺ヨ櫄鎷熷彉閲?OLS 鍙ｅ緞涓嶅悓锛屽繀椤讳互 Stata 17 瀹為檯杈撳嚭涓哄噯锛屽苟鍦ㄦ姤鍛婁腑鍐欐竻楠岃瘉璇佹嵁銆?- 鑻?FE + cluster 鐨勮嚜鐢卞害淇瀛樺湪涓嶇‘瀹氭€э紝鍏堢敤娴嬭瘯閿佸畾 Stata 缁撴灉锛屽啀瀹炴柦浠ｇ爜锛屼笉瑕佸厛鐚滃叕寮忋€?- 鑻ュ湪鏈疆鍐呭彂鐜?Phase 2 鏃犳硶鏁翠綋鏀跺彛锛屽繀椤绘槑纭寚鍑哄崱鐐瑰睘浜?`p2_fe_basic` 杩樻槸 `p2_fe_cluster`锛屼笉寰楁ā绯婃眹鎶モ€滈儴鍒嗗畬鎴愨€濄€?