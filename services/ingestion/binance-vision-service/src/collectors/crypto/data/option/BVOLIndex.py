"""Option / BVOLIndex（占位）

# 对齐官方目录语义
# - data/option/daily/BVOLIndex/{SYMBOL}/{SYMBOL}-BVOLIndex-YYYY-MM-DD.csv
#
# 样本事实
# - CSV 有 header
# - 列：calc_time,symbol,base_asset,quote_asset,index_value
#
# 输出
# - data/option/daily/BVOLIndex/{SYMBOL}/{SYMBOL}-BVOLIndex-{date}.csv
#
# 落库目标（Raw/物理层）
# - crypto.raw_option_bvol_index
"""

from __future__ import annotations


def collect() -> None:
    raise NotImplementedError
