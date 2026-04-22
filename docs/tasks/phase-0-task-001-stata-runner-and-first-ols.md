# 浠诲姟鍗★細Phase 0 Task 001 - Stata Runner 涓庨涓?OLS 鍙岃窇鏍蜂緥

## 鍩烘湰淇℃伅

- 浠诲姟鍚嶇О锛歋tata runner 鏈€灏忛摼璺笌棣栦釜 OLS 榛勯噾鏍蜂緥
- 鎵€灞為樁娈碉細Phase 0
- 瀵瑰簲 backlog 鏉＄洰锛?  - 椤圭洰楠ㄦ灦涓庡寘缁撴瀯
  - Stata runner 鏈€灏忛摼璺?  - 缁撴灉 schema 涓庡簭鍒楀寲
  - 棣栦釜 OLS 鍙岃窇鏍蜂緥
- 浼樺厛绾э細P0
- 鎵ц浜猴細QwenCode
- 瀹℃煡浜猴細Codex

## 鏈疆鐩爣

浜や粯涓€涓渶灏忎絾瀹屾暣鐨勫彲楠岃瘉闂幆锛?
1. 寤虹珛 Python 椤圭洰楠ㄦ灦
2. 寤虹珛缁撴灉 schema 楠ㄦ灦
3. 瀹炵幇鍙墽琛岀殑 Stata runner 鏈€灏忛摼璺?4. 瀹屾垚棣栦釜 `regress` 瀵圭収鏍蜂緥
5. 璁?Python 涓?Stata 鑷冲皯鏈変竴鏉″瓧娈电骇鍙岃窇娴嬭瘯璺戦€?
鏈疆鐩爣涓嶆槸瀹炵幇瀹屾暣 OLS 搴擄紝鑰屾槸鍏堟墦閫氣€滃彲寮€鍙戙€佸彲娴嬭瘯銆佸彲姣斿鈥濈殑宸ョ▼鍥炶矾銆?
## 蹇呰鏂囨。

QwenCode 寮€濮嬪墠蹇呴』闃呰锛?
1. `docs/project-charter.md`
2. `docs/architecture/overview.md`
3. `docs/architecture/result-schema.md`
4. `docs/architecture/stata-compatibility.md`
5. `docs/testing/testing-strategy.md`
6. `docs/testing/test-case-catalog.md`
7. `docs/phases/phase-0-bootstrap.md`
8. `docs/operations/qwencode-playbook.md`
9. `docs/operations/review-gates.md`

## 寤鸿鏂囦欢缁撴瀯

鏈疆寤鸿鍒涘缓鎴栬ˉ榻愪互涓嬭矾寰勶細

- `src/stataflow/__init__.py`
- `src/stataflow/results/`
- `src/stataflow/stata_runner/`
- `tests/`
- `tests/golden/`
- `stata/`
- `stata/cases/`
- `stata/output/`
- `pyproject.toml`

鑻?QwenCode 璁や负鐩綍鍚嶉渶瑕佸井璋冿紝鍙互璋冩暣锛屼絾涓嶅緱鏀瑰彉鍥涘眰鏋舵瀯鍚箟銆?
## 鏈疆鎵ц姝ラ

### Step 1: 寤虹珛椤圭洰楠ㄦ灦

闇€瑕佸畬鎴愶細

- 鍒涘缓 `src/` 鍖呯粨鏋?- 鍒涘缓 `tests/` 缁撴瀯
- 鍒涘缓 Stata 鐩稿叧鐩綍
- 閫夋嫨鏈€灏忎緷璧栫鐞嗘柟妗堝苟鍒濆鍖栭厤缃?
鏈浜у嚭锛?
- 鍙鍏ョ殑鏈€灏?Python 鍖?- 鍙繍琛岀殑鏈€灏忔祴璇曢厤缃?
### Step 2: 寤虹珛 result schema 鏈€灏忓疄鐜?
闇€瑕佸畬鎴愶細

- 鍒涘缓缁撴灉瀵硅薄楠ㄦ灦
- 鏀寔搴忓垪鍖栦负 dict 鎴?JSON 鍏煎缁撴瀯
- 鑷冲皯瑕嗙洊 `model`銆乣sample`銆乣fit`銆乣coefficients`銆乣variance`銆乣provenance` 杩欎簺椤跺眰鍧?
鏈娴嬭瘯锛?
- round-trip 鎴栧簭鍒楀寲 smoke test

### Step 3: 瀹炵幇 Stata runner 鏈€灏忛摼璺?
闇€瑕佸畬鎴愶細

- 鑳芥壘鍒?Stata 鍙墽琛屾枃浠?- 鑳界敓鎴愭渶灏?`.do` 鏂囦欢
- 鑳借皟鐢?Stata 鎵瑰鐞嗚繍琛?- 鑳借鍙栭€€鍑虹姸鎬佸拰杈撳嚭鏂囦欢

绾︽潫锛?
- 涓嶈鍦?runner 涓紪鐮佸叿浣撳洖褰掗€昏緫
- 璺緞閰嶇疆灏介噺鍙弬鏁板寲锛屼笉瑕佹妸鍗曚竴鏈満璺緞鍐欐鍦ㄦ牳蹇冧唬鐮侀噷

鏈娴嬭瘯锛?
- runner smoke test

### Step 4: 鍒涘缓棣栦釜 OLS 瀵圭収鏍蜂緥

闇€瑕佸畬鎴愶細

- 鍑嗗涓€涓渶灏忔暟鎹泦
- 缂栧啓 Stata `.do` 鏂囦欢杩愯 `regress`
- 瀵煎嚭缁撴瀯鍖栫粨鏋滐紝鑷冲皯鍖呮嫭绯绘暟鍚戦噺銆佸崗鏂瑰樊鐭╅樀銆佹牱鏈暟鍜岃嚜鐢卞害
- 鍦?Python 渚у垱寤哄搴旈粍閲戞祴璇?
鏈绾︽潫锛?
- 涓嶅緱鍙瘮杈冪郴鏁?- 鑷冲皯姣旇緝锛歚params`銆乣cov`銆乣nobs`銆乣df_model`銆乣df_resid`

### Step 5: 鍥炲～鏂囨。鐘舵€?
闇€瑕佸畬鎴愶細

- 鍦?`docs/testing/test-case-catalog.md` 鏇存柊 `p0_min_ols_auto` 鐨勭姸鎬佷笌瀹為檯浜х墿璺緞
- 鑻ョ洰褰曠粨鏋勪笌璁″垝鏈夊亸宸紝鍦ㄥ搴旈樁娈垫墜鍐屾垨浠诲姟缁撴灉涓鏄?
## 鏈疆寤鸿娴嬭瘯椤哄簭

1. 鍖呭鍏?smoke test
2. result schema 搴忓垪鍖栨祴璇?3. runner smoke test
4. 棣栦釜 OLS 鍙岃窇娴嬭瘯

## QwenCode 鍥炴姤鏍煎紡

鏈疆缁撴潫鍚庯紝QwenCode 蹇呴』鑷冲皯鍥炴姤锛?
- 淇敼鏂囦欢鍒楄〃
- 鏂板娴嬭瘯鍒楄〃
- Stata 鍙墽琛屾枃浠跺畾浣嶆柟寮?- Stata 鍙岃窇鍛戒护鎴栬Е鍙戞柟寮?- 鍙岃窇鎴愬姛瀛楁
- 灏氭湭瀹屾垚鐨勫瓧娈?- 鏄惁瀛樺湪闇€瑕?Codex 瑁佸喅鐨勯棶棰?
## 鏈疆楠屾敹鏍囧噯

- Python 鍖呴鏋跺凡寤虹珛
- result schema 鏈€灏忓疄鐜板彲搴忓垪鍖?- runner 鏈€灏忛摼璺彲鎵ц
- `p0_min_ols_auto` 宸茶惤鍦板苟閫氳繃
- 鏂囨。鐘舵€佸凡鍥炲～

## 鏈疆绂佹浜嬮」

- 涓嶈瀹炵幇瀹屾暣绾挎€фā鍨?API
- 涓嶈鎻愬墠杩涘叆 robust銆乧luster銆丗E
- 涓嶈涓轰簡鈥滃厛璺戦€氣€濊€岀粫杩囩粨鏋勫寲缁撴灉瀵煎嚭
- 涓嶈淇敼椤圭洰绔犵▼鎴栧叕鍏?API 鍘熷垯

## 澶辫触涓庡崌绾ф潯浠?
鍑虹幇浠ヤ笅浠讳竴鎯呭喌锛孮wenCode 搴斿仠姝㈠苟涓婃姤锛?
- 鏃犳硶绋冲畾璋冪敤 Stata 17
- Stata 瀵煎嚭缁撴瀯鏃犳硶鏄犲皠鍒?result schema
- 闃舵鏂囨。涓庡疄闄呭疄鏂藉瓨鍦ㄧ粨鏋勬€у啿绐?- 闇€瑕佹敼鍔ㄧ粨鏋?schema 鐨勯《灞傜粨鏋?