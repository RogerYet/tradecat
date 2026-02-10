# ACCEPTANCE - ingestion 重构迁移验收

## A. 成功路径（Happy Path）

1) **WS 1m K线采集链路可跑**
- 能启动订阅、缓冲、按窗口 flush、写入 raw（或现有 candles 表域）
- 证据：日志包含“批量写入 N 条”并且 DB 中目标时间窗有数据

2) **缺口巡检 + 补齐可跑**
- 在可控的短时间窗内，能检测缺口并触发 ZIP/REST 补齐尝试
- 证据：gap_found 计数增长 + 补齐写入条数增长

3) **5m 期货指标采集可跑**
- 能并发拉取、批量写入、并输出请求成功/失败计数

## B. 对齐验证（必须有基线对比）

> 迁移不是“跑起来就算赢”，必须证明“口径一致”。

- 固定：单币种 `BTCUSDT` + 固定时间窗 `T0~T1` + 固定 interval `1m`
- 对齐断言（至少三条）：
  1) 时间锚点一致：所有点对齐到分钟边界（UTC），且与旧实现的 bucket_ts 一致
  2) 字段一致：open/high/low/close/volume/trade_count 等字段对齐（允许浮点误差阈值）
  3) 幂等一致：重复跑 2 次，row count 不增长（upsert 生效）

## C. 安全性（硬门槛）

- 源仓库 `/home/lenovo/.projects/tradecat` 业务代码不变（只读）
- 源仓库 `config/.env`、`libs/database/**.db` 不被写入（mtime/hash 不变）

## D. 边缘路径（至少 3 个）

1) cryptofeed 不可用：应降级为 REST（或明确失败但不污染源仓库）。  
2) 数据库不可用：应快速失败并给出可读错误（不陷入重试风暴）。  
3) 429/418 限流：退避/熔断生效，且 metrics 中能观察到失败计数。  

