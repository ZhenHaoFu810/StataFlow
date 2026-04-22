# Codex Review: 瀹¤涓荤嚎浠诲姟鍖?004锛坄ivreghdfe` Phase B锛?
## 缁撹

鏈疆 **鎵撳洖**銆?
闃诲鍘熷洜涓嶆槸 `ivreghdfe` 鐨勭畻娉曟垨娴嬭瘯澶辫触锛岃€屾槸 **source-backed 鏍稿績璇佹嵁鏂囨。 `docs/research/ivreghdfe-source-map.md` 浠嶄繚鐣欏澶?Phase A 鏃х粨璁猴紝涓庡綋鍓嶄唬鐮併€佹敮鎸佺煩闃靛拰娴嬭瘯鐘舵€佷笉涓€鑷?*銆傚湪涓荤嚎瀹¤妯″紡涓嬶紝杩欑 source map 涓嶄竴鑷翠笉鑳芥斁琛屽埌涓嬩竴鏉″懡浠や富绾裤€?
## 鎴戝疄闄呭鏍哥殑鍐呭

### Fresh verification

```powershell
python -m pytest tests/test_compat_stata_iv.py tests/test_hdfe_synthetic.py tests/golden/test_w2_ivreghdfe_basic.py tests/golden/test_w2_ivreghdfe_cluster.py tests/golden/test_w2_ivreghdfe_real_panel.py -v
python -m pytest tests -v
```

缁撴灉锛?
- `ivreghdfe` 鐩稿叧涓撻」 鈫?`75 passed`
- 鍏ㄩ噺 鈫?`676 passed`

### Spot check

鎴戦澶栨鏌ヤ簡锛?
- `src/stataflow/estimators/iv.py`
- `src/stataflow/compat/stata/iv.py`
- `docs/research/ivreghdfe-source-map.md`
- `docs/command-support-matrix/ivreghdfe.md`
- `workspace/current-task/REPORT.md`

褰撳墠鐪熷疄瀹炵幇宸茬粡鏀寔骞堕€氳繃娴嬭瘯锛?
- wrapper: `noconstant`, `keepsingletons`
- estimator `predict(type="xb"|"xbd"|"residuals"|"d"|"dresiduals")`
- `vce="ols"|"robust"|"cluster"`

鎵€浠ヨ繖杞樆濉炵偣涓嶆槸瀹炵幇涓荤嚎锛岃€屾槸 source map 浠嶆湭鍚屾銆?
## 闃诲闂

### 1. syntax mapping 浠嶆妸 `noconstant` 璇存垚鍐呴儴濮嬬粓鍔犲父鏁?
`docs/research/ivreghdfe-source-map.md` 绗?3.1 鑺傝繕鍐欑潃锛?
- Python 绛変环瀹炵幇 `sets add_constant=True`

浣嗗綋鍓?wrapper 宸茬粡鍏紑鏀寔锛?
- `noconstant`
- 骞朵笖浼犲叆 `IVAbsorbingOLS(add_constant=not noconstant)`

杩欎細鐩存帴璇鍚庣画 source-backed 瀹¤銆?
### 2. 鈥淜nown Phase A Simplifications鈥?浠嶅啓鐫€ `No predict beyond xb`

鍚屼竴鏂囦欢绗?6 鑺傝繕淇濈暀锛?
- `No predict beyond xb`

浣嗗綋鍓嶄唬鐮併€佹祴璇曞拰鏀寔鐭╅樀閮藉凡缁忔敮鎸侊細

- `xb`
- `xbd`
- `residuals`
- `d`
- `dresiduals`

杩欏睘浜庢槑鏄捐繃鏈熺粨璁恒€?
### 3. `_cons` 鏄犲皠娈典粛淇濈暀鏃ч€昏緫

绗?3.8 鑺備粛鍐欙細

- Python 浼氶€氳繃 `T` 鐭╅樀鎭㈠ `_cons`

浣嗗綋鍓嶄唬鐮侀噷锛?
- `IVAbsorbingOLS.fit()` 鏄庣‘娉ㄩ噴 `ivreghdfe never reports _cons`
- `_coef_names` 鍙寘鍚?`x_endog + x_exog`

涔熷氨鏄锛岃繖閲屼繚鐣欑殑鏄棫瀹炵幇鐥曡抗锛屼笉鍐嶇鍚堝綋鍓嶅叕鍏辫涔夈€?
## 杩斿伐瑕佹眰

鏈杩斿伐 **涓嶈姹傛柊澧炰换浣?`ivreghdfe` 绠楁硶瀹炵幇**銆傚彧瑕佹眰鎶婁互涓嬫枃妗ｆ敹鍙ｅ埌涓庡綋鍓嶇湡瀹炲疄鐜颁竴鑷达細

- `docs/research/ivreghdfe-source-map.md`
- 濡傛湁蹇呰锛屽井璋?`workspace/current-task/REPORT.md` 涓 source map 瀹屾暣搴︾殑琛ㄨ堪

## 杩斿伐閫氳繃鏍囧噯

鍙湁鍚屾椂婊¤冻浠ヤ笅鏉′欢锛屾墠鍏佽杩涘叆涓嬩竴姝ヤ富绾夸换鍔★細

1. `ivreghdfe-source-map.md` 涓嶅啀淇濈暀 `add_constant=True` 鐨勬棫缁撹锛岃€屾槸鏄庣‘璇存槑 `noconstant` 鐨勫綋鍓嶅叕鍏辫涔夈€?2. `ivreghdfe-source-map.md` 鐨?鈥淜nown Phase A Simplifications鈥?涓嶅啀鎶?`predict` 璇存垚浠呮敮鎸?`xb`銆?3. `ivreghdfe-source-map.md` 鐨?`_cons` 鏄犲皠鎻忚堪涓庡綋鍓嶄唬鐮佸拰鏀寔鐭╅樀涓€鑷淬€?4. 閲嶆柊璺戯細
   - `python -m pytest tests/test_compat_stata_iv.py tests/test_hdfe_synthetic.py tests/golden/test_w2_ivreghdfe_basic.py tests/golden/test_w2_ivreghdfe_cluster.py tests/golden/test_w2_ivreghdfe_real_panel.py -v`
   - `python -m pytest tests -v`
   鍏ㄩ儴閫氳繃銆?