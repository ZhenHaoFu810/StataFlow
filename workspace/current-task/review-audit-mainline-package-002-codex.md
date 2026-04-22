# Codex Review锛氬璁′富绾夸换鍔″寘 002锛坄reghdfe` 瀹屾暣搴︽帹杩?Phase B锛?
## 瀹℃煡缁撹

**缁撹锛氭墦鍥炪€?*

鏈疆 `reghdfe` 鐨勫疄鐜颁富绾垮拰娴嬭瘯涓荤嚎鍩烘湰鎴愮珛锛屼絾杩樹笉鑳戒笅鏀句笅涓€姝ヤ富绾夸换鍔★紝鍘熷洜涓嶆槸绠楁硶澶辫触锛岃€屾槸 **鏍稿績璇佹嵁閾炬枃妗ｆ病鏈夊畬鍏ㄦ敹鍙?*銆?
鎴戝疄闄呭璺戜簡锛?
```powershell
python -m pytest tests/test_hdfe_synthetic.py -v
python -m pytest tests/golden/test_p3_reghdfe_basic.py tests/golden/test_p3_reghdfe_cluster.py tests/golden/test_p3_reghdfe_two_fe.py tests/golden/test_p3_reghdfe_real_panel.py tests/golden/test_p3_reghdfe_keepsingletons.py -v
python -m pytest tests -v
```

缁撴灉鍒嗗埆涓猴細

- `25 passed`
- `74 passed`
- `663 passed`

杩欒鏄庯細

- `keepsingletons`
- `noconstant`
- `predict(xb/xbd/d/residuals/dresiduals)`

杩欐壒鏂板鑳藉姏鍦ㄥ疄鐜板眰鍜屾祴璇曞眰閮藉凡缁忕珯浣忋€?
闃诲鐐瑰湪浜庯細浠诲姟鍖?002 鏄庣‘瑕佹眰鍚屾鏇存柊 `reghdfe-source-map.md` 涓?`reghdfe.md`锛屼絾杩欎袱浠芥枃妗ｄ粛淇濈暀浜嗕笌褰撳墠瀹炵幇鐩稿啿绐佺殑鏃х粨璁恒€?
## 闃诲闂

### 1. `reghdfe-source-map.md` 鍐呴儴浠嶄繚鐣欐棫鐨?Phase A `predict` 缁撹

鏂囦欢浣嶇疆锛?
- [docs/research/reghdfe-source-map.md](</D:/OneDrive - SAIF/PhD3/StataFlow/docs/research/reghdfe-source-map.md>)

闂锛?
- 绗?4 鑺備粛鍐欙細
  - `xb` = 鍚?FE 鐨勫畬鏁撮娴?  - `d` / `xbd` = 鏈疄鐜?- 杩欏拰褰撳墠鐪熷疄浠ｇ爜銆乻upport matrix銆乻ynthetic tests銆佹姤鍛婇兘鐭涚浘銆?
杩欎笉鏄帾杈為棶棰橈紝鑰屾槸 source-backed 瀹¤鏂囨。鍐呴儴鑷浉鐭涚浘锛屼細鐩存帴璇鍚庣画鐨勬簮鐮佺骇瀹屾暣澶嶇幇宸ヤ綔銆?
### 2. `reghdfe-source-map.md` 鐨?wrapper parameter matrix 浠嶄繚鐣欐棫鐨勬湭鏀寔缁撹

鍚屼竴鏂囦欢涓紝绗?5 鑺備粛鍐欙細

- `keepsingletons`锛歸rapper 涓嶆毚闇?- `noconstant`锛歸rapper 鎬绘槸鍔犲父鏁?
浣嗗綋鍓嶅疄闄呬唬鐮侊細

- `stataflow.compat.stata.reghdfe(..., keepsingletons=True)`
- `stataflow.compat.stata.reghdfe(..., noconstant=True)`

閮藉凡鏀寔銆?
### 3. `reghdfe.md` 椤堕儴瀹屾暣搴︾姸鎬佷粛鍋滅暀鍦?鈥淧hase A Subset鈥?
鏂囦欢浣嶇疆锛?
- [docs/command-support-matrix/reghdfe.md](</D:/OneDrive - SAIF/PhD3/StataFlow/docs/command-support-matrix/reghdfe.md>)

闂锛?
- 椤堕儴浠嶅啓 `Partial / Phase A Subset`
- 浣嗘湰杞换鍔℃湰韬氨鏄鎺ㄨ繘鍒?Phase B锛屽苟涓旂‘瀹炶ˉ榻愪簡 Phase B 琛屼负

濡傛灉瀹屾暣搴︾姸鎬佷笉鏀癸紝鍚庣画涓荤嚎浠诲姟鍜屽璁＄粨璁洪兘浼氬け鐪熴€?
## 闈為樆濉炶鏄?
- [workspace/current-task/REPORT.md](</D:/OneDrive - SAIF/PhD3/StataFlow/workspace/current-task/REPORT.md>) 鐨?fresh run 鏁板瓧鐜板湪宸茬粡鏇存柊涓?`663 passed`锛岃繖涓€鐐逛笉鍐嶉樆濉炪€?- 褰撳墠鎴戞病鏈夊彂鐜版湰杞柊澧?`reghdfe` 璇箟瀛樺湪蹇呴』闃诲鐨勬暟瀛﹂敊璇€?
## 杩斿伐瑕佹眰

鏈杩斿伐鍙仛鏂囨。涓庣姸鎬佹敹鍙ｏ紝涓嶅啀鎵╁疄鐜帮細

1. 缁熶竴淇 `docs/research/reghdfe-source-map.md`
2. 鏇存柊 `docs/command-support-matrix/reghdfe.md` 鐨勫畬鏁村害鐘舵€佷笌鏂囧瓧鎻忚堪
3. 纭繚 source map / support matrix / report / 褰撳墠浠ｇ爜鍥涜€呬竴鑷?
閫氳繃鍚庯紝鎴戝啀鍐冲畾鏄惁涓嬫斁涓嬩竴姝ヤ富绾夸换鍔★紙`ppmlhdfe` 瀹屾暣搴︽帹杩涳級銆?