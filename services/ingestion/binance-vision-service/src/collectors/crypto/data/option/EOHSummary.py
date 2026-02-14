"""Option / EOHSummary（占位）

# 对齐官方目录语义
# - data/option/daily/EOHSummary/{UNDERLYING}/{UNDERLYING}-EOHSummary-YYYY-MM-DD.csv
#
# 样本事实
# - CSV 有 header
# - 列：date,hour,symbol,underlying,type,strike,open,high,low,close,volume_contracts,volume_usdt,
#       best_bid_price,best_ask_price,best_bid_qty,best_ask_qty,best_buy_iv,best_sell_iv,
#       mark_price,mark_iv,delta,gamma,vega,theta,openinterest_contracts,openinterest_usdt
#
# 输出
# - data/option/daily/EOHSummary/{UNDERLYING}/{UNDERLYING}-EOHSummary-{date}.csv
#
# 落库目标（Raw/物理层）
# - crypto.raw_option_eoh_summary
"""

from __future__ import annotations


def collect() -> None:
    raise NotImplementedError
