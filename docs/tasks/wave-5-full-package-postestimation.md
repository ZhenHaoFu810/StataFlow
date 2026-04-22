# Wave 5 Full Package: Postestimation

## 鍩烘湰淇℃伅

- 浠诲姟鍚嶇О锛歐ave 5 鏁村寘浠诲姟锛歅ostestimation
- 鎵€灞炲懡浠ゆ棌锛歚Postestimation`
- 浼樺厛绾э細P5
- 鎵ц浜猴細Claude Code
- 瀹℃煡浜猴細Codex

## 浠诲姟鐩爣

涓€娆℃€ф帹杩涙暣涓?`Wave 5`锛屼絾蹇呴』鎸夊唴閮?`Stage A / B / C` 椤哄簭瀹屾垚锛屼笉鑳借烦闃舵瀹ｇО鏁村寘瀹屾垚銆?
鏈?wave 鐨勭洰鏍囦笉鏄鍒?Stata 鍏ㄩ儴 postestimation锛岃€屾槸浜や粯涓€涓?**楂橀銆佸彲鍙岃窇銆佺粨鏋滆涔夋竻鏅?* 鐨勬渶灏忓瓙闆嗭細

- `predict`
- `margins` 楂橀瀛愰泦

## 鍐呴儴闃舵

### Stage A: Research Closure

蹇呴』鍏堣ˉ榻愮爺绌舵枃妗ｏ紝鍐嶈繘鍏ュ疄鐜帮細

- `docs/research/predict.md`
- `docs/research/margins.md`

姣忎唤鏂囨。鑷冲皯鍐欐竻锛?
- 鏀寔鐨勬ā鍨嬫棌
- 鏀寔鐨?Stata 璇硶瀛愰泦
- 杈撳嚭瀵硅薄涓庡瓧娈佃涔?- 鏁板瀹氫箟
- 鎺ㄦ柇鍙ｅ緞
- 鏄庣‘涓嶆敮鎸佺殑閫夐」

鍚屾椂蹇呴』鍦?`docs/testing/test-case-catalog.md` 棰勭櫥璁帮細

- synthetic 鏍蜂緥
- real-data 鏍蜂緥
- 姣忎釜鏍蜂緥鐨勪富瑕侀闄╃偣

### Stage B: Minimum Implementation

#### `predict`

鏈€灏忓瓙闆嗚姹傦細

- 绾挎€х被妯″瀷锛?  - `predict, xb`
  - `predict, residuals`
- 浜屽厓/璁℃暟妯″瀷锛?  - `predict, xb`
  - `predict, pr` 鎴?`predict, mu`
- 瑕嗙洊鐨?Python 妯″瀷鑷冲皯鍖呮嫭锛?  - `OLS`
  - `FixedEffectsOLS` / `AbsorbingOLS`
  - `Logit`
  - `Probit`
  - `Poisson`
  - `PPMLHDFE`

鏄庣‘涓嶅仛锛?
- 鎵€鏈?Stata `predict` 閫夐」鍏ㄩ泦
- influence / score / stdp / hat 绛夐珮绾ц緭鍑?- 鍥惧舰鎺ュ彛

#### `margins`

鏈€灏忓瓙闆嗚姹傦細

- `margins, dydx(*)`
- `margins, atmeans`
- 棣栧厛瑕嗙洊锛?  - `Logit`
  - `Probit`
  - `Poisson`
- 瀵圭嚎鎬фā鍨嬶紝楂橀瀛愰泦鍙帴鍙楋細
  - `margins, dydx(*)` 缁撴灉鍥炲埌绯绘暟鏈韩鎴栫瓑浠峰璞?
鏄庣‘涓嶅仛锛?
- `marginsplot`
- factor-variable 鍏ㄥ巻鍙插吋瀹?- 楂樼淮浜や簰鏁堝簲鍥?- bootstrap / delta-method 浠ュ澶嶆潅鎺ㄦ柇鎵╁睍

### Stage C: Real-Data Validation And Hardening

鑷冲皯鍋氬埌锛?
- `predict` 鏈?synthetic + real-data 鍙岀嚎楠岃瘉
- `margins` 鏈?synthetic + real-data 鍙岀嚎楠岃瘉
- 鑷冲皯瑕嗙洊 1 涓嚎鎬х湡瀹炴暟鎹牱渚?- 鑷冲皯瑕嗙洊 1 涓潪绾挎€х湡瀹炴暟鎹牱渚?
浼樺厛澶嶇敤椤圭洰鍐呭凡鏈夊叕寮€鏁版嵁锛?
- `Fama-French 3 factors`
- `wagepan`
- `Grunfeld`
- `Mroz`
- `crime1`
- `countymurders`

## 鐪熷疄鏁版嵁瑕佹眰

鎵€鏈?real-data 楠岃瘉蹇呴』锛?
- 浣跨敤鏈湴鍏紑鏁版嵁
- 鍦ㄦ姤鍛婁腑璁板綍 Stata 鍛戒护涓?Python 璋冪敤
- 璇存槑瀵归綈瀛楁
- 璇存槑浠讳綍鍓╀綑鍋忓樊鍙婂叾鏁板鍘熷洜

## 鍏佽淇敼鐨勬枃浠?
- `src/stataflow/` 涓嬩笌 postestimation 鐩稿叧鏂囦欢
- `tests/golden/` 涓嬫柊澧炵殑 Wave 5 娴嬭瘯
- `docs/research/predict.md`
- `docs/research/margins.md`
- `docs/testing/test-case-catalog.md`
- `docs/backlog.md`
- `workspace/current-task/REPORT.md`

## 绂佹浜嬮」

- 涓嶈鎵╁睍鍒?`marginsplot`
- 涓嶈鎵╁睍鍒板鏉?bootstrap / simulation inference
- 涓嶈鎶婃墍鏈?Stata `predict` 瀛愰€夐」閮戒竴娆″仛瀹?- 涓嶈寮曞叆鏈枃妗ｅ寲鐨勬ā鍨嬩笓鐢ㄧ壒娈婅涓?- 涓嶈鎶婃湭楠岃瘉瀛楁鍐欐垚鈥滃彲鎺ュ彈鈥濆悗鐩存帴鏀捐

## 寮哄埗楠岃瘉鍛戒护

瀹屾垚鍚庤嚦灏戣繍琛岋細

```powershell
python -m pytest tests/golden/test_w5_predict_* -v
python -m pytest tests/golden/test_w5_margins_* -v
python -m pytest tests -v
```

濡傛灉鍛藉悕涓嶅悓锛屽繀椤诲湪鎶ュ憡閲岄€愰」鍒楀嚭瀹為檯鍛戒护銆?
## 鍥炴姤瑕佹眰

鎶ュ憡蹇呴』鍒嗕负 `Stage A / Stage B / Stage C`锛屾槑纭啓娓咃細

1. `predict` 瑕嗙洊浜嗗摢浜涙ā鍨嬩笌杈撳嚭绫诲瀷
2. `margins` 瑕嗙洊浜嗗摢浜涙ā鍨嬩笌璇箟瀛愰泦
3. 姣忎釜鏂板 synthetic 鏍蜂緥鐨勯闄╃偣
4. 姣忎釜 real-data 鏍蜂緥鐨勬暟鎹潵婧愪笌 Stata/Python 鍛戒护
5. 鍝簺瀛楁涓?Stata 涓ユ牸瀵归綈锛屽摢浜涘瓧娈佃嫢浠嶆湁鍋忓樊锛屽亸宸師鍥犳槸浠€涔?6. 鍏ㄩ噺娴嬭瘯缁撴灉

## 閫氳繃鏍囧噯

鍙湁鍚屾椂婊¤冻浠ヤ笅鏉′欢锛孋odex 鎵嶄細鏀捐鏁翠釜 Wave 5锛?
1. `predict` 涓?`margins` 鐨勭爺绌舵枃妗ｅ畬鎴愩€?2. `predict` 涓?`margins` 閮芥湁 synthetic 榛勯噾鏍蜂緥銆?3. `predict` 涓?`margins` 閮借嚦灏戞湁 1 涓湡瀹炲叕寮€鏁版嵁鍙岃窇鏍蜂緥銆?4. 鍏ㄩ噺娴嬭瘯閫氳繃銆?5. `docs/backlog.md` 涓?`docs/testing/test-case-catalog.md` 鐘舵€佷竴鑷淬€?6. 娌℃湁鏈В閲婄殑鍏抽敭缁熻鍙ｅ緞鍋忓樊銆?