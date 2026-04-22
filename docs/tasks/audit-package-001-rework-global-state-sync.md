# 瀹¤鍚庝换鍔″寘 001 杩斿伐锛歚rdrobust` 鍏ㄥ眬鐘舵€佷笌璇佹嵁閾惧悓姝?
## 1. 杩斿伐鐩爣

鏈杩斿伐**涓嶈姹傜户缁墿 `rdrobust` 绠楁硶涓昏矾寰?*銆?
涓荤洰鏍囧彧鏈変竴涓細

鎶?`rdrobust` 浠庘€滃眬閮ㄥ疄鐜板凡瀹屾垚鈥濇帹杩涘埌鈥滈」鐩叏灞€鐘舵€併€佹祴璇曠洰褰曘€乻upport matrix 鍏ュ彛銆佹墽琛屾姤鍛娾€濆叏閮ㄥ悓姝ヤ竴鑷淬€?
## 2. 蹇呴』瀹屾垚鐨勫唴瀹?
### A. 鍚屾鍏ㄥ眬浠诲姟姹?
鏇存柊 [docs/backlog.md](</D:/OneDrive - SAIF/PhD3/StataFlow/docs/backlog.md>)锛?
- 姝ｅ紡澧炲姞 `rdrobust` 鏉＄洰
- 鏄庣‘瀹冨綋鍓嶇殑鍛戒护鏃忓綊灞?- 鏄庣‘瀹冨綋鍓嶇殑鐘舵€佷笉鏄?`done/full`锛岃€屾槸涓?support matrix 涓€鑷寸殑瀛愰泦鐘舵€?
### B. 鍚屾娴嬭瘯鏍蜂緥鐩綍

鏇存柊 [docs/testing/test-case-catalog.md](</D:/OneDrive - SAIF/PhD3/StataFlow/docs/testing/test-case-catalog.md>)锛?
- 澧炲姞 `rdrobust` 鐨?synthetic case
- 澧炲姞 `rdrobust` 鐨?real-data / official-example case
- 鐘舵€佸簲涓庡綋鍓嶇湡瀹炴祴璇曟儏鍐典竴鑷?
### C. 鍚屾 support matrix 鎬诲叆鍙?
鏇存柊 [docs/command-support-matrix/README.md](</D:/OneDrive - SAIF/PhD3/StataFlow/docs/command-support-matrix/README.md>)锛?
- 鍦?`Research Archives` 娈佃惤涓姞鍏?`rdrobust-source-map.md`
- 濡傛湁蹇呰锛岃皟鏁?`Alpha 鈥?Partial` 鐨勭姸鎬佽鏄庯紝浣垮叾涓?`rdrobust.md` 淇濇寔涓€鑷?
### D. 淇鎵ц鎶ュ憡

鏇存柊 [workspace/current-task/REPORT.md](</D:/OneDrive - SAIF/PhD3/StataFlow/workspace/current-task/REPORT.md>)锛?
- 鎾ゅ洖鈥滃叚鍛戒护瀹屾暣搴︾姸鎬佸凡缁熶竴鏀跺彛鈥濊繖绫讳笉鍑嗙‘琛ㄨ堪
- 鍥炲～鏈€鏂?fresh run 缁撴灉
- 鏄庣‘璇存槑鏈疆杩斿伐鍙仛鐘舵€佸悓姝ワ紝涓嶆墿绠楁硶闈?
## 3. 涓嶉渶瑕佸仛鐨勪簨

鏈疆涓嶈棰濆鍋氾細

- `rdrobust` 鏂扮畻娉曟墿灞?- `fuzzy` / `bwselect` / `cluster` 鏂板姛鑳?- 鍏朵粬 vendor 鍛戒护鍔熻兘鎵╁睍

闄ら潪浣犲湪鍚屾鏂囨。鏃跺彂鐜颁細鐩存帴褰卞搷鐜版湁缁撹鐨勪弗閲嶉敊璇€?
## 4. 楠岃瘉瑕佹眰

鑷冲皯鎵ц骞跺洖鎶ワ細

```powershell
python -m pytest tests/test_rdrobust.py -v
python -m pytest tests -v
```

濡傛灉浠ｇ爜鏈韩娌℃湁鍙樺寲锛屽彲浠ュ湪鎶ュ憡閲岃鏄庘€渇resh run 涓昏鐢ㄤ簬纭杩斿伐鏈紩鍏ュ洖褰掆€濄€?
## 5. 瀹屾垚鏍囧噯

鏈疆杩斿伐閫氳繃鐨勬潯浠舵槸锛?
- `rdrobust` 宸叉寮忚繘鍏?backlog
- `rdrobust` 宸茶繘鍏?test-case-catalog
- `rdrobust-source-map.md` 宸茶繘鍏?command-support-matrix README 鐨勬€诲叆鍙?- 鎶ュ憡涓嶅啀澶稿ぇ瀹屾垚搴?
