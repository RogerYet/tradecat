# STATUS - 进度真相源

状态: Not Started

## 关键证据（本任务创建时已知）

- 旧 WS 采集 flush window: `services/data-service/src/collectors/ws.py:37`
- CandleEvent.timestamp 语义: `services/data-service/src/adapters/cryptofeed.py:49`（= candle.start）
- COPY+temp-table upsert: `services/data-service/src/adapters/timescale.py:76`~`:125`

## 阻塞项

- Blocked by: 无

