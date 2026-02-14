"""缺口修复（repair）采集卡片。

约定：
- repair 不是官方数据集目录的一部分，但它是“治理闭环”的关键环节。
- repair 只做：消费 `crypto.ingest_gaps` → 触发权威回填 → 关闭 gap。
"""

