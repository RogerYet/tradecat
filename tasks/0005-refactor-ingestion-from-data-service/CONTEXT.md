# CONTEXT - 旧 data-service 到新 ingestion 的映射（基于证据）

## 1) 旧 data-service 的真实结构（证据）

旧服务模块列表（源参考，只读）：

- `services/data-service/src/collectors/ws.py`：WS 1m K线采集（批量 flush + gap backfill）
- `services/data-service/src/collectors/backfill.py`：缺口扫描与补齐（ZIP + REST/CCXT）
- `services/data-service/src/collectors/metrics.py`：期货指标采集（REST 并发）
- `services/data-service/src/adapters/timescale.py`：Timescale 写入（COPY + temp table + upsert）
- `services/data-service/src/adapters/ccxt.py`：REST 拉取 K 线、符号加载与标准化
- `services/data-service/src/adapters/cryptofeed.py`：cryptofeed WS 适配（CandleEvent.timestamp=candle.start）

可复核证据（执行 Agent）：

- `find services/data-service/src -maxdepth 3 -type f -name '*.py' | sort`
- `rg -n "TimescaleAdapter" services/data-service/src | head`

## 2) 旧实现的关键“正确性语义”（迁移不能丢）

从 `collectors/ws.py` 可提取的硬语义：

- CandleEvent 的时间戳是 **candle.start（开盘时间）**：`services/data-service/src/adapters/cryptofeed.py:49`
- 写入采用 **3 秒时间窗口批量 flush**：`services/data-service/src/collectors/ws.py:37`~`:115`
- 缺口巡检是后台线程，回溯天数自适应，最大 7 天：`services/data-service/src/collectors/ws.py:157`~`:170`

从 `adapters/timescale.py` 可提取的硬语义：

- K线 upsert 冲突键：`(exchange, symbol, bucket_ts)`：`services/data-service/src/adapters/timescale.py:89`
- 批量写入策略：TEMP TABLE + COPY + INSERT ON CONFLICT：`services/data-service/src/adapters/timescale.py:76`~`:125`

## 3) 为什么“直接 copy 过去用”不够（你这次要求的点）

旧服务是“按运行形态组织”（collectors + adapters + sys.path hack）：

- 运行形态耦合：`sys.path.insert` 在多个 collectors 顶部出现（例如 `services/data-service/src/collectors/ws.py:19`）
- 采集/写入/回填耦合在同一个进程对象里（WSCollector 同时负责订阅、缓冲、写库、补齐策略）

新结构要求“按职责分层”（providers/jobs/storage）：

- providers：只负责拉取与标准化（WS/REST/ZIP），不写库
- storage：只负责写 raw_*（COPY/upsert），不做拉取与重试策略
- jobs：编排与观测（flush window、watermark、gap scan、retry/backoff）

## 4) 新结构中的目标落点（目录级契约）

建议落地文件（示例命名，执行 Agent 可调整，但职责不变）：

- `/home/lenovo/tradecat/tradecat/ingestion/providers/binance/ws_cryptofeed.py`
- `/home/lenovo/tradecat/tradecat/ingestion/providers/binance/rest_ccxt.py`
- `/home/lenovo/tradecat/tradecat/ingestion/providers/binance/vision_zip.py`
- `/home/lenovo/tradecat/tradecat/ingestion/storage/timescale_writer.py`
- `/home/lenovo/tradecat/tradecat/ingestion/jobs/candles_ws_1m.py`
- `/home/lenovo/tradecat/tradecat/ingestion/jobs/backfill_gaps.py`
- `/home/lenovo/tradecat/tradecat/ingestion/jobs/futures_metrics_5m.py`
- `/home/lenovo/tradecat/tradecat/ingestion/cli.py`

## 5) 风险量化表

| 风险点 | 严重程度 | 触发信号 | 缓解方案 |
| :--- | :---: | :--- | :--- |
| 时间语义漂移（start/close 搞反） | High | 对齐验证中同一时间窗数据点对不上 | 以旧实现为基线，固定 `open_ts=candle.start`；写 3 个对齐用例 |
| 批量写入性能下降 | High | 同样 300 symbols/分钟写入耗时暴涨 | 直接迁移 COPY+temp table 写法；保留批量窗口 |
| gap backfill 逻辑被拆散后失效 | Medium | gap 检测/补齐不再触发或误补 | 将 gap scan/backfill 作为独立 job，明确输入输出与水位线 |
| 迁移过程中污染源仓库 | High | `.projects/tradecat` 下出现新 logs 或 config 变化 | 全程运行根固定到 `/home/lenovo/tradecat`；并用 hash/mtime 证伪 |

