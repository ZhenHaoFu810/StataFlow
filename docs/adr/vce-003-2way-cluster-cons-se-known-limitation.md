# VCE-002/003/004：HDFE 常数项与 MAP 聚类修复记录

## 状态

**Fixed（2026-06-12）。** 文件名保留是为了维持历史链接稳定；本文替代此前的 Known Limitation 决策。

## 原问题

- VCE-002：文档声称大 FE 的 MAP 常数项方差依赖近似。
- VCE-003：二维聚类时 `_cons` SE 在合成数据偏差 7.98%，在 wagepan 偏差 6.44%。
- VCE-004：文档声称 MAP cluster slope 允许约 0.5% 偏差。

## 根因

此前根因判断不正确。偏差并不要求重构 HDFE 内核，也不是 LSDV 与 MAP 在统计意义上的结构性差异。

本机安装的 `reghdfe.mata` 显示：

1. `reghdfe_extend_b_and_xx()` 用 regression-through-means 恢复 `_cons` 和完整 bread。
2. `reghdfe_vce_cluster()` 先在标准化变量尺度计算多路聚类 VCE。
3. `reghdfe_fix_psd()` 对完整 VCE 截断负特征值，再恢复经过同类修正的 slope 子矩阵。
4. PSD 修正完成后，才把 VCE 还原到原始变量尺度。

特征值截断不具备尺度不变性。旧实现直接在原始尺度修正，并额外尝试保持所有报告方差不变，因此 slope 可以对齐而 `_cons` SE 系统性偏离。

## 修复

- `fix_psd_reghdfe()` 改为复现上游 CGM 修正顺序。
- `AbsorbingOLS` 在 PSD 修正前使用 Stata 的样本标准差尺度，修正后再还原。
- 删除未被调用的旧 MAP 常数方差近似实现，避免两套冲突算法继续并存。
- 将二维聚类 slope 与 `_cons` 拆分测试，全部改为普通硬断言，不再使用 `xfail`。

## 证据

- Stata validation case `w7_reghdfe_2way_cluster`：17 passed。
- Stata validation case `w7_reghdfe_2way_cluster_real`：15 passed。
- Stata validation case `w12_map_small_sample`：7 passed，MAP 与 LSDV 在 OLS、robust、cluster 场景按机器精度一致。
- 合成和 wagepan 的 `_cons` SE 均满足项目 `<1e-6` 相对误差标准。

## 决策

VCE-002、VCE-003、VCE-004 均关闭。不得恢复旧的常数方差近似、原始尺度 PSD 修正或相关 `xfail`。
