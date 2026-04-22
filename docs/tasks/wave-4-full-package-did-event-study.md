# Wave 4 Full Package: DID / Event Study Extensions

## 鍩烘湰淇℃伅

- 浠诲姟鍚嶇О锛歐ave 4 鏁村寘浠诲姟锛欴ID / Event Study Extensions
- 鎵€灞炲懡浠ゆ棌锛歚DID / Event Study Extensions`
- 浼樺厛绾э細P4
- 鎵ц浜猴細Claude Code
- 瀹℃煡浜猴細Codex

## 浠诲姟鐩爣

涓€娆℃€ф帹杩涙暣涓?Wave 4锛屼絾蹇呴』鎸夊唴閮ㄩ樁娈甸『搴忓畬鎴愶紝涓嶈兘璺抽樁娈靛绉版暣鍖呭畬鎴愩€?
鏈?wave 鐨勭洰鏍囧懡浠や负锛?
- `did_imputation`
- `eventstudyinteract`
- `csdid`

鐩爣涓嶆槸澶嶅埢姣忎釜鍛戒护鐨勫叏閮ㄥ巻鍙查€夐」锛岃€屾槸浜や粯涓€涓?*鏈€灏忎絾缁熻鍙ｅ緞娓呮銆佸彲鍙岃窇楠岃瘉銆佽兘杩涘叆鍥炲綊娴嬭瘯**鐨勫吋瀹瑰瓙闆嗐€?
## 鍐呴儴闃舵

### Stage A: Research Closure

蹇呴』鍏堝畬鎴愪互涓嬬爺绌跺伐浣滐紝鍐嶈繘鍏ュ疄鐜帮細

- 琛ラ綈鎴栭噸鍐欎笅鍒楃爺绌舵枃妗ｏ細
  - `docs/research/did_imputation.md`
  - `docs/research/eventstudyinteract.md`
  - `docs/research/csdid.md`
- 瀵规瘡涓懡浠ゅ啓娓咃細
  - 鐩爣 estimand
  - 鏁版嵁缁撴瀯瑕佹眰
  - 璇嗗埆鍋囪
  - 鏍稿績浼拌鍏紡
  - 鎺ㄦ柇鍙ｅ緞
  - Stata/绀惧尯鍛戒护鐨勫叧閿€夐」
  - 鏈€灏忓吋瀹瑰瓙闆?  - 鏄庣‘涓嶅仛鐨勯€夐」
- 鍦?`docs/testing/test-case-catalog.md` 棰勭櫥璁帮細
  - synthetic 鏍蜂緥
  - real-data 鏍蜂緥
  - 瀵归綈瀛楁

### Stage B: Minimum Implementation

瀵逛笁涓懡浠ら兘鍋氭渶灏忓疄鐜帮紝浣嗚寖鍥村繀椤绘敹绱с€?
#### `did_imputation`

鏈€灏忓瓙闆嗚姹傦細

- staggered adoption panel
- balanced 鎴栬繎骞宠　 panel
- 鍗曟鍚告敹澶勭悊
- 鍗曚綅鑱氱被鏍囧噯璇?- event time 鍔ㄦ€佹晥搴旇緭鍑?
鏄庣‘涓嶅仛锛?
- repeated cross-section
- 澶氬€煎鐞?- 澶氬眰 bootstrap
- 澶嶆潅 aggregation 鍙樹綋

#### `eventstudyinteract`

鏈€灏忓瓙闆嗚姹傦細

- Sun-Abraham interaction-weighted event-study
- cohort 脳 relative-time 缁撴瀯
- 鍗曚綅 FE + 鏃堕棿 FE
- 鍗曚綅鑱氱被鏍囧噯璇?- 鍩哄噯鏈熸樉寮忓彲鎺?
鏄庣‘涓嶅仛锛?
- 澶氬悜 cluster
- 楂樼骇 postestimation
- 鍥惧舰杈撳嚭

#### `csdid`

鏈€灏忓瓙闆嗚姹傦細

- panel 鐗堟湰浼樺厛
- group-time ATT 杈撳嚭
- 鑷冲皯鏀寔涓€涓父鐢?aggregation
- 鍗曚綅鑱氱被鏍囧噯璇?
鏄庣‘涓嶅仛锛?
- repeated cross-section
- doubly robust 鐨勬墍鏈夊垎鏀彉浣撲竴娆℃€у叏寮€
- bootstrap-based 鍏ㄩ儴鎺ㄦ柇閫夐」

### Stage C: Real-Data Validation And Hardening

姣忎釜鍛戒护閮藉繀椤昏嚦灏戞湁锛?
- 1 涓?synthetic 榛勯噾鏍蜂緥
- 1 涓湡瀹炲叕寮€鏁版嵁鏍蜂緥

骞跺畬鎴愶細

- Stata / Python 鍙岃窇
- 瀛楁绾у榻愭姤鍛?- 宸茬煡宸紓鏂囨。鍖?- `docs/backlog.md` 涓?`docs/testing/test-case-catalog.md` 鐘舵€佸悓姝?
## 鐪熷疄鏁版嵁瑕佹眰

浼樺厛浣跨敤鍏紑銆佸彲澶嶇幇銆佸甫鏈夌粡鍏?staggered adoption 缁撴瀯鐨勬暟鎹€?
鎺ㄨ崘鍊欓€夛細

- Castle Doctrine / stand-your-ground 椋庢牸宸炲勾闈㈡澘
- minimum wage / policy adoption 宸炲勾闈㈡澘
- 鍏紑鍘垮勾鏀跨瓥 panel
- Stata / Wooldridge / teaching datasets 涓彲澶嶇幇鐨?staggered treatment 瀛愰泦

瑕佹眰锛?
- 鏁版嵁蹇呴』钀藉埌鏈湴鐮旂┒鐩綍
- 鏂囨。涓褰曟潵婧愩€佹竻娲椼€佸彉閲忓畾涔夈€丼tata 鍛戒护銆丳ython 鍛戒护

## 鍏佽淇敼鐨勬枃浠?
- `src/stataflow/estimators/` 涓嬩笌 DID / event study 鐩稿叧鐨勬柊鏂囦欢
- `src/stataflow/__init__.py`
- `src/stataflow/estimators/__init__.py`
- `tests/golden/` 涓嬫柊澧炵殑 Wave 4 娴嬭瘯
- `docs/research/` 涓嬬殑 Wave 4 鏂囨。
- `docs/testing/test-case-catalog.md`
- `docs/backlog.md`
- `workspace/current-task/REPORT.md`

## 绂佹浜嬮」

- 涓嶈鎵╁睍鍒?`drdid`銆乣did2s`銆乣bacondecomp`銆乣honestdid`
- 涓嶈鍦ㄦ湰 wave 娣峰叆 `predict`銆乣margins`銆佸浘褰㈡帴鍙?- 涓嶈涓€娆℃€у疄鐜版墍鏈?bootstrap / simulation / randomization inference
- 涓嶈寮曞叆澶氬悜 cluster
- 涓嶈鎶婃湭楠岃瘉鐨勭粺璁″樊寮傚啓鎴愨€滃彲鎺ュ彈鈥濆悗鐩存帴鏀捐

## 寮哄埗楠岃瘉鍛戒护

瀹屾垚鍚庡繀椤昏嚦灏戣繍琛岋細

```bash
python -m pytest tests/golden/test_w4_did_imputation_basic.py -v
python -m pytest tests/golden/test_w4_eventstudyinteract_basic.py -v
python -m pytest tests/golden/test_w4_csdid_basic.py -v
python -m pytest tests -v
```

濡傛灉鏂板浜嗘洿澶?Wave 4 golden tests锛屽繀椤诲湪鎶ュ憡涓€愰」鍒楀嚭骞惰繍琛屻€?
## 鍥炴姤瑕佹眰

鎶ュ憡蹇呴』鍒?Stage A / Stage B / Stage C 涓夋锛屾槑纭啓娓咃細

1. 涓変釜鍛戒护鍚勮嚜鐨勬渶灏忓疄鐜拌竟鐣?2. 姣忎釜鍛戒护鐨勮瘑鍒亣璁句笌 estimand
3. 姣忎釜鍛戒护鏂板浜嗗摢浜?synthetic 鏍蜂緥
4. 姣忎釜鍛戒护鐢ㄤ簡鍝簺鐪熷疄鍏紑鏁版嵁
5. 鍝簺瀛楁涓?Stata 瀵归綈锛屽摢浜涘瓧娈佃嫢浠嶆湁鍋忓樊锛屽亸宸師鍥犳槸浠€涔?6. 鍏ㄩ噺娴嬭瘯缁撴灉

## 閫氳繃鏍囧噯

鍙湁鍚屾椂婊¤冻浠ヤ笅鏉′欢锛孋odex 鎵嶄細鏀捐鏁翠釜 Wave 4锛?
- `did_imputation`銆乣eventstudyinteract`銆乣csdid` 閮藉畬鎴愮爺绌舵。妗?- 涓変釜鍛戒护閮借嚦灏戞湁 synthetic 榛勯噾鏍蜂緥
- 涓変釜鍛戒护閮借嚦灏戞湁涓€涓湡瀹炲叕寮€鏁版嵁鍙岃窇鏍蜂緥
- 鍏ㄩ噺娴嬭瘯閫氳繃
- `docs/backlog.md` 涓?`docs/testing/test-case-catalog.md` 鐘舵€佷竴鑷?- 娌℃湁鏈В閲婄殑鍏抽敭缁熻鍙ｅ緞鍋忓樊
