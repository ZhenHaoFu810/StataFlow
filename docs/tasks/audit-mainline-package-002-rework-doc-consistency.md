# 瀹¤涓荤嚎浠诲姟鍖?002 杩斿伐锛歚reghdfe` 鏂囨。涓庤瘉鎹摼涓€鑷存€ф敹鍙?
## 1. 杩斿伐鑳屾櫙

`reghdfe` Phase B 鐨勪唬鐮佸疄鐜板拰娴嬭瘯涓荤嚎宸茬粡閫氳繃锛屼絾涓荤嚎浠诲姟鍖?002 浠嶆湭鏀捐锛屽洜涓烘牳蹇冭瘉鎹枃妗ｆ病鏈夊畬鍏ㄦ敹鍙ｃ€?
褰撳墠涓昏鐭涚浘鏄細

- `docs/research/reghdfe-source-map.md` 閲屽悓鏃跺瓨鍦ㄦ棫鐨?Phase A 缁撹鍜屾柊鐨?Phase B 缁撹
- `docs/command-support-matrix/reghdfe.md` 椤堕儴瀹屾暣搴︾姸鎬佷粛鍐欐垚 `Phase A Subset`

杩欎細鐩存帴鐮村潖鈥滄簮鐮佹敮鎾戙€佹暟瀛﹀彛寰勪紭鍏堚€濈殑瀹¤閾俱€?
## 2. 鏈疆鍙仛浠€涔?
鍙仛鏂囨。涓€鑷存€ц繑宸ワ紝涓嶆墿瀹炵幇锛屼笉鏀圭畻娉曘€?
蹇呴』鏀跺彛浠ヤ笅鏂囦欢锛?
- [docs/research/reghdfe-source-map.md](</D:/OneDrive - SAIF/PhD3/StataFlow/docs/research/reghdfe-source-map.md>)
- [docs/command-support-matrix/reghdfe.md](</D:/OneDrive - SAIF/PhD3/StataFlow/docs/command-support-matrix/reghdfe.md>)
- 濡傛湁蹇呰锛屽井璋?[workspace/current-task/REPORT.md](</D:/OneDrive - SAIF/PhD3/StataFlow/workspace/current-task/REPORT.md>) 閲岀殑鎺緸锛屼絾涓嶈閲嶅啓宸叉纭殑娴嬭瘯缁撴灉

## 3. 蹇呴』瀹屾垚鐨勪慨姝?
### A. 淇 source map 鐨?`predict` 鏄犲皠

`docs/research/reghdfe-source-map.md` 绗?4 鑺傚綋鍓嶄粛淇濈暀鏃ц娉曪紝蹇呴』鏀规垚涓庡綋鍓嶅疄鐜颁竴鑷达細

- `xb` = 浠?reported 绯绘暟鐨勭嚎鎬ч娴嬶紝涓嶅惈 FE 璐＄尞
- `xbd` = 鍚?FE 鐨勫畬鏁撮娴?- `d` = `xbd - xb`
- `residuals` = `y - xbd`
- `dresiduals` = `y - xb`
- `stdp` 浠嶆湭瀹炵幇

涓嶈兘缁х画淇濈暀 鈥渀d` / `xbd` 鏈疄鐜扳€?鎴?鈥渀xb` 鍚?FE鈥?杩欑鏃х粨璁恒€?
### B. 淇 source map 鐨?wrapper parameter matrix

蹇呴』鎶婁互涓嬫潯鐩敼鍒颁笌褰撳墠浠ｇ爜涓€鑷达細

- `keepsingletons`
- `noconstant`

涓嶈兘鍐嶅啓鎴?wrapper 鏈毚闇叉垨鎬绘槸鍔犲父鏁般€?
### C. 鏇存柊 `reghdfe` support matrix 鐨勫畬鏁村害鐘舵€?
`docs/command-support-matrix/reghdfe.md` 椤堕儴瀹屾暣搴︾姸鎬佸繀椤讳粠鏃х殑 `Phase A Subset` 鏇存柊鎴愪笌褰撳墠浠诲姟闃舵涓€鑷寸殑琛ㄨ堪銆?
鎺ㄨ崘鍐欐硶鏂瑰悜锛?
- 浠嶇劧 `Partial`
- 浣嗗凡杩涘叆 `Phase B`
- 鏄庣‘鍐欏嚭鏈疆鏂扮撼鍏ョ殑琛屼负锛?  - `keepsingletons`
  - `noconstant`
  - expanded `predict`

### D. 淇濊瘉鍥涙柟涓€鑷?
淇畬鍚庡繀椤讳繚璇佷互涓嬪洓鏂逛笉鍐嶄簰鐩稿啿绐侊細

1. `src/stataflow/compat/stata/hdfe.py`
2. `src/stataflow/estimators/absorbing_ols.py`
3. `docs/research/reghdfe-source-map.md`
4. `docs/command-support-matrix/reghdfe.md`

## 4. 楠岃瘉瑕佹眰

鏈疆涓嶇敤閲嶈窇鍏ㄩ噺 golden matrix锛屼絾鑷冲皯瑕佸洖鎶ワ細

```powershell
python -m pytest tests/test_hdfe_synthetic.py -v
python -m pytest tests -v
```

骞跺湪鎶ュ憡涓槑纭啓锛?
- 淇簡鍝簺鏂囨。鍐茬獊
- 淇悗 source map / support matrix / code 濡備綍涓€涓€瀵瑰簲

## 5. 瀹屾垚鏍囧噯

鏈疆閫氳繃鐨勬渶浣庢爣鍑嗭細

- `reghdfe-source-map.md` 涓嶅啀淇濈暀涓庡綋鍓嶅疄鐜板啿绐佺殑鏃х粨璁?- `reghdfe.md` 鐨勫畬鏁村害鐘舵€佷笉鍐嶅仠鐣欏湪 `Phase A`
- 鎶ュ憡銆乻upport matrix銆乻ource map銆佷唬鐮佸洓鑰呬竴鑷?
鍋氬埌杩欎竴鐐瑰悗锛孋odex 鍐嶅喅瀹氭槸鍚︿笅鏀句笅涓€姝ヤ富绾夸换鍔★細`ppmlhdfe` 瀹屾暣搴︽帹杩涖€?