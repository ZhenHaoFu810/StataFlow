# Review: 瀹¤鍚庝换鍔″寘 001

## 缁撹

鏈疆**涓嶉€氳繃**锛屾殏涓嶄笅鏀句笅涓€浠诲姟鍖呫€?
鍘熷洜涓嶆槸 `rdrobust` 鏍稿績瀹炵幇娌¤窇閫氥€傜浉鍙嶏紝褰撳墠 fresh run 琛ㄦ槑锛?
- `python -m pytest tests/test_rdrobust.py -v` 鈫?`11 passed`
- `python -m pytest tests -v` 鈫?`500 passed`

鑰屼笖 `rdrobust` 鐨勬渶灏?sharp RD 涓昏矾寰勩€亀rapper 鏆撮湶銆乻ynthetic/real-data 娴嬭瘯閮藉凡缁忚惤鍦般€?
褰撳墠闃诲鐐瑰湪浜庯細**鍏ㄥ眬鐘舵€佷笌鏂囨。娉ㄥ唽娌℃湁鏀跺彛鍒扳€渧endor 鍏懡浠ゅ畬鏁村害缁熶竴鏇存柊鈥濈殑浠诲姟瑕佹眰**銆傝繖浼氱洿鎺ュ奖鍝嶅悗缁鏌ヤ笌寮€婧愭矡閫氾紝鍥犳涓嶈兘鏀捐銆?
## 闃诲闂

### 1. `rdrobust` 娌℃湁琚悓姝ヨ繘鍏ㄥ眬浠诲姟姹?
- [docs/backlog.md](</D:/OneDrive - SAIF/PhD3/StataFlow/docs/backlog.md>) 浠嶆病鏈?`rdrobust` 鏉＄洰
- 褰撳墠浠诲姟鍖呰姹傛妸 vendor 鍏懡浠ゅ畬鏁村害鐘舵€佺粺涓€鏀跺彛
- 鐜板湪 support matrix 閲屾湁 `rdrobust`锛屼絾 backlog 涓嶇煡閬撳畠瀛樺湪

杩欐剰鍛崇潃椤圭洰鍏ㄥ眬灞傞潰瀵?`rdrobust` 鐨勭姸鎬佺鐞嗕粛鐒舵槸缂哄け鐨勩€?
### 2. `rdrobust` 娌℃湁杩涘叆娴嬭瘯鏍蜂緥鐩綍娓呭崟

- [docs/testing/test-case-catalog.md](</D:/OneDrive - SAIF/PhD3/StataFlow/docs/testing/test-case-catalog.md>) 娌℃湁浠讳綍 `rdrobust` case
- 褰撳墠浠诲姟鍖呰姹?synthetic + real-data 娴嬭瘯璇佹嵁閾炬敹鍙?- 瀹為檯娴嬭瘯宸茬粡鏈?`tests/test_rdrobust.py`锛屼絾鐩綍娓呭崟娌℃湁鐧昏

杩欎細瀵艰嚧鍚庣画鈥滄祴璇曡鐩栫洏鐐光€濆拰鈥滃畬鏁村害瀹¤鈥濇棤娉曚緷璧栫粺涓€鐩綍銆?
### 3. Command Support Matrix 鎬诲叆鍙ｆ病鏈夋妸 `rdrobust-source-map.md` 绾冲叆 research archive 鍒楄〃

- [docs/command-support-matrix/README.md](</D:/OneDrive - SAIF/PhD3/StataFlow/docs/command-support-matrix/README.md>) 宸叉柊澧?`rdrobust` 鍛戒护琛?- 浣?`Research Archives` 娈佃惤浠嶅彧鍒楀嚭 5 涓?source map锛屾病鏈?`rdrobust-source-map.md`

杩欒鏄庘€渟upport matrix / source map / 鍏ㄥ眬鍏ュ彛涓夊悜涓€鑷存€р€濆皻鏈畬鍏ㄦ敹鍙ｃ€?
### 4. 鎵ц鎶ュ憡澶稿ぇ浜嗏€淰endor 鍏懡浠ゅ畬鏁村害鐘舵€佺粺涓€鏀跺彛鈥?
- [workspace/current-task/REPORT.md](</D:/OneDrive - SAIF/PhD3/StataFlow/workspace/current-task/REPORT.md>) 澹扮О鍏懡浠ゅ畬鏁村害鐘舵€佸凡缁熶竴鏀跺彛
- 浣?backlog 鍜?test-case-catalog 鐨勫叏灞€娉ㄥ唽鏈悓姝?
鍥犳杩欎唤鎶ュ憡杩樹笉鑳戒綔涓哄共鍑€鐨勫叧鍗曡瘉鎹€?
## 涓嶆瀯鎴愰樆濉炵殑閮ㄥ垎

浠ヤ笅鍐呭鎴戣涓哄凡缁忔垚绔嬶紝涓嶈姹傝繑宸ワ細

- `rdrobust` estimator 宸插瓨鍦ㄤ笖鍙鍏?- `stataflow.compat.stata.rdrobust()` wrapper 宸插瓨鍦ㄤ笖鍙皟鐢?- `tests/test_rdrobust.py` 鏈?synthetic + real-data + negative tests
- 鍏ㄩ噺 `pytest` 鏃犲洖褰?- `rdrobust` support matrix 涓?source map 涓讳綋鍐呭宸插叿澶囧彲瀹℃煡鎬?
## 杩斿伐瑕佹眰

鏈杩斿伐涓嶈姹傜户缁敼 `rdrobust` 绠楁硶鏈韩锛岄櫎闈炰綘鍦ㄥ悓姝ュ叏灞€鐘舵€佹椂鍙戠幇鏂扮殑鏁板闂銆?
蹇呴』瀹屾垚锛?
1. 鍦?[docs/backlog.md](</D:/OneDrive - SAIF/PhD3/StataFlow/docs/backlog.md>) 涓寮忕櫥璁?`rdrobust`
2. 鍦?[docs/testing/test-case-catalog.md](</D:/OneDrive - SAIF/PhD3/StataFlow/docs/testing/test-case-catalog.md>) 涓櫥璁?`rdrobust` 鐨?synthetic 涓?real-data case
3. 鍦?[docs/command-support-matrix/README.md](</D:/OneDrive - SAIF/PhD3/StataFlow/docs/command-support-matrix/README.md>) 鐨?research archive 鍒楄〃涓ˉ鍏?`rdrobust-source-map.md`
4. 鏇存柊 [workspace/current-task/REPORT.md](</D:/OneDrive - SAIF/PhD3/StataFlow/workspace/current-task/REPORT.md>)锛屾挙鍥炩€滃凡缁熶竴鏀跺彛鈥濈殑涓嶅噯纭〃杩帮紝骞跺洖濉渶鏂伴獙璇佺粨鏋?
## 閫氳繃鏉′欢

涓嬫鎴戜細閲嶇偣妫€鏌ワ細

- `rdrobust` 鏄惁宸茬粡姝ｅ紡杩涘叆 backlog
- `rdrobust` 娴嬭瘯璇佹嵁鏄惁杩涘叆 test-case-catalog
- support matrix 鎬诲叆鍙ｆ槸鍚︿笌 source map 涓€鑷?- 鎶ュ憡鏄惁涓庝粨搴撳綋鍓嶇姸鎬佷竴鑷?
濡傛灉杩欎簺鐘舵€佹敹鍙ｅ畬鎴愶紝鎴戦璁′笅涓€杞彲浠ョ洿鎺ラ€氳繃锛屽苟涓嬫斁涓嬩竴浠诲姟鍖呫€?
