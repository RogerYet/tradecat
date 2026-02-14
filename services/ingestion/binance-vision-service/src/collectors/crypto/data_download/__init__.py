"""Binance Vision 历史数据下载补齐（代码版目录树）。

# 约定
# - 该目录结构与 realtime 的 data/ 保持一致（同一数据集两种采集模式）。
# - download 模式用于：按日/月从官方历史站点下载 ZIP/CSV → 解压 → 落盘 → 导入 raw 表。
# - 本阶段仅保留 Raw/基元数据集（写入 crypto.raw_*）。
"""
