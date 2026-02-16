# PRD：Telegram 卡片 → Google Sheets 公共看板（卡片块 x,y 渲染 + 全字段无遗漏审计）

## 0) 一句话定义

把现有 Telegram（TG）前端“卡片消息”同步到一个 **Google Sheets（公开只读）** 工作簿中：
- **展示面**：在 `dashboard` 里按时间顺序把每张卡片画成一个二维块（固定列宽、可变行高，x,y 堆叠）。
- **事实面**：以“索引 + EAV（键值）+ 外部 Blob 引用”的方式 **完整留存所有字段与原始内容（无遗漏）**，支持筛选统计、审计追溯、以及重放重建 dashboard。

> 关键前提：公开可读 ≠ 匿名可写。任何自动写入必须通过有编辑权限的身份（Apps Script Webhook 或 Service Account）。

---

## 1) 背景与问题

### 1.1 现状
- TG 内持续产出多类卡片：排行榜/快照/信号/异常/运行状态等。
- 数据以消息流存在：不利于批量检索、跨币种对比、统计、复盘与审计。

### 1.2 你提出的“表格化”本质
你要的不是“把卡片解析成一行表”，而是同时满足两件事：
1) **像 TG 一样看**：卡片占据固定列段、可变高度，按时间顺序堆叠。
2) **像数据库一样查**：任何字段都不丢（包括未知字段、未来新增字段、原始文本/JSON）。

---

## 2) 目标 / 非目标

### 2.1 目标（必须）
1) **全卡片覆盖**：TG 现有卡片类型都能写入（至少以 raw + EAV 的形式落盘）。
2) **全字段无遗漏**：字段集合不可预设，必须做到“来什么记什么”，且能回溯原始内容。
3) **幂等写入**：重复投递同一卡片不会产生重复事实记录；dashboard 不出现重复块。
4) **旁路不阻塞**：写 Sheets 失败不影响 TG 主链路（outbox + 重试）。
5) **可重建**：dashboard 属于派生展示面，可由事实表重放重建。

### 2.2 非目标（明确不做）
- 不把逐笔/订单簿等高频明细作为 Sheets 主仓。
- 不在 Sheets 内做强事务、强一致的数据库能力。

---

## 3) 关键约束（Google Sheets 硬限制）

### 3.1 写入身份
公开表格只能匿名只读；自动写入必须走：
- A) Apps Script Webhook（推荐默认：Sheets 侧提供 HTTP 函数）
- B) Service Account + Sheets API（备选：服务端直连 Google API）

### 3.2 容量与性能
Sheets 有单元格字符上限、工作簿 cell 总量上限（约 1000 万）、脚本执行时间与配额限制。

**因此结论：**
“无遗漏”不能靠把所有 raw 文本/JSON 都塞进单元格。必须支持：
- 表内存“索引/摘要/结构化字段”
- 超长内容落到外部 Blob（Google Drive 文件或对象存储），表内存引用与 hash 校验

---

## 4) 总体方案（标准分层：事实表 + 渲染表）

### 4.1 工作簿 Sheet 规划（标准）

```text
+------------------+--------------------------------------------------------+
| Sheet            | 职责                                                   |
+------------------+--------------------------------------------------------+
| dashboard         | 展示面：卡片块 x,y 渲染（固定列宽、可变高度）           |
| cards_index       | 索引面：一卡一行（幂等键/时间/类型/TG 链接/渲染坐标）   |
| card_fields_eav   | 事实面：卡片级“所有字段”EAV（字段无限扩展，不遗漏）     |
| card_rows         | 事实面：表格型卡片的“明细行骨架”（rank/symbol 等）      |
| row_fields_eav    | 事实面：明细行的“所有字段”EAV（字段无限扩展，不遗漏）   |
| blobs_index       | 外部大字段引用：raw_text/raw_json（URL + hash + size）  |
| meta              | 状态：dashboard_next_row、schema_version、统计等        |
+------------------+--------------------------------------------------------+
```

### 4.2 为什么要 EAV（键值表）
你要求“全部卡片全部字段无遗漏”，字段集合不可预先穷举；EAV 可以保证：
- 新字段出现无需改表结构
- 字段用 `field_path`（层级路径）表达，不丢语义
- dashboard 渲染失败也不影响事实落盘

---

## 5) 数据契约（Schema & 幂等）

### 5.1 幂等键（card_key）
必须稳定可复现，优先级推荐：
1) 卡片对应 TG 消息：`tg:{chat_id}:{message_id}`
2) 非 TG 消息但有 run：`run:{run_id}:{card_type}:{ts_epoch_ms}`
3) 否则：`hash:{sha256(canonical_json)}`

### 5.2 `cards_index`（一卡一行，主索引，append-only）

```text
card_key (PK)
ts_utc, ts_shanghai
source_service
card_type
title
dataset, period, sort_key, sort_order, limit
rows_count
dash_sheet, dash_col_l, dash_col_r, dash_row_y, dash_height
tg_chat_id, tg_message_id, tg_url
run_id
raw_text_blob_ref, payload_blob_ref
created_at_utc
```

### 5.3 `card_fields_eav`（卡片字段 EAV）

```text
eav_key (PK) = {card_key}:{seq}
card_key
scope          (card/header/params/hint/raw/...)
field_path     (例如 header.update_time / params.period / hint.text)
value_type     (text/number/bool/json/blob_ref)
value_text
value_number
value_json
blob_ref_id
```

### 5.4 `card_rows` + `row_fields_eav`（表格型卡片明细）
当卡片内部有“排行表/明细表”时，必须额外落明细层，保证可筛选/透视：

`card_rows`：
- `row_key (PK)`：`{card_key}:r:{rank}`（最稳）或 `{card_key}:r:{symbol}`
- `card_key, rank, symbol, symbol_full, row_ts_utc`

`row_fields_eav`：
- `eav_key (PK)`：`{row_key}:{field_path}` 或 `{row_key}:{seq}`
- `row_key, card_key, field_path, value_type, value_* , blob_ref_id`

### 5.5 `blobs_index`（外部大字段引用）
用于“无遗漏”的底座：

```text
blob_ref_id (PK) = blob:{sha256}
card_key (nullable)
row_key  (nullable)
kind     (tg_raw_text/payload_json/render_snapshot/...)
mime
storage_url
sha256
size_bytes
created_at_utc
```

---

## 6) dashboard 渲染标准（你要的 x,y + i）

### 6.1 固定列宽
`dashboard` 选定固定列区间 `[COL_L..COL_R]`（例如 N..Z），所有卡片都写在这一段列中。

### 6.2 固定版式（强约束，脚本好写）
卡片明细行数 = N，则卡片高度：`i = 7 + N`，并带 1 行空行分隔：
- y+0：title（合并 COL_L..COL_R）
- y+1：update（合并）
- y+2：sort（合并）
- y+3：明细表头（真实列，不合并）
- y+4..y+3+N：明细行（真实列）
- y+4+N：hint（合并）
- y+5+N：last_update（合并）
- y+6+N：空行

下一张卡片起点：`y_next = y + (7 + N)`

### 6.3 `meta.dashboard_next_row`（唯一写入指针）
`dashboard_next_row` 必须在 Webhook 侧用锁保护（并发写入会撞块）。

---

## 7) 接口设计（推荐默认：Apps Script Webhook）

### 7.1 为什么推荐 Webhook
- 你要求“Google 在线表格作为函数”：Apps Script 的 `doPost()` 天然就是函数入口。
- 服务端只要 HTTP POST JSON，不需要在服务端维护 Google API 凭证复杂度。

### 7.2 Endpoint
- `POST https://script.google.com/.../exec`

### 7.3 鉴权（必须）
建议默认：HMAC + 时间窗 + nonce
- Header：
  - `X-TC-Timestamp`: Unix ms
  - `X-TC-Nonce`: UUID
  - `X-TC-Signature`: `hex(hmac_sha256(secret, timestamp + '.' + nonce + '.' + body))`
- 校验：
  - timestamp 在 ±5min 内
  - nonce 未使用过（简化版：存最近 N 个 nonce + 5min TTL）

### 7.4 请求体（CardEvent，schema_version=1）
```json
{
  "schema_version": 1,
  "card_key": "tg:123:456",
  "ts_utc": "2026-02-17T05:15:00Z",
  "source_service": "telegram-service",
  "card_type": "supertrend_rank",
  "header": {
    "title": "📈 超级趋势数据",
    "update_time": "2026-02-17 05:15:00",
    "sort_desc": "15m 趋势强度(🔽)"
  },
  "params": {
    "dataset": "trend",
    "period": "15m",
    "sort_key": "trend_strength",
    "sort_order": "desc",
    "limit": 10
  },
  "table": {
    "columns": ["rank", "symbol", "trend_strength", "price"],
    "rows": [
      {"rank": 1, "symbol": "BTCUSDT", "trend_strength": 3.14, "price": 623.02}
    ]
  },
  "hint": { "text": "..." },
  "tg": { "chat_id": 123, "message_id": 456, "url": "https://t.me/xxx/456" },
  "raw": {
    "telegram_text_full": "（可选，可能很长）",
    "payload_json_full": { "..." : "..." }
  }
}
```

### 7.5 响应体
```json
{
  "ok": true,
  "card_key": "tg:123:456",
  "idempotent": true,
  "dashboard": { "sheet": "dashboard", "col_l": "N", "col_r": "Z", "row_y": 1201, "height": 17 }
}
```

### 7.6 幂等行为
- 若 `cards_index` 已存在该 `card_key`：
  - 返回 `idempotent=true`
  - 不重复写事实、不重复渲染
  - （可选增强）支持 `force_render=true` 用于重建 dashboard

---

## 8) 处理流程（端到端）

### 8.1 服务端（telegram-service）侧：旁路 outbox
1) 卡片生成并发送 TG 成功
2) 生成 CardEvent（结构化 + raw + rows）
3) 写入 outbox（SQLite/文件队列）
4) 后台 worker 批量 flush 到 Webhook（失败指数退避重试）

### 8.2 Webhook（Apps Script）侧：先事实后渲染
顺序必须固定，才能保证“无遗漏 + 可重建”：
1) 鉴权（HMAC）
2) 幂等检查（cards_index 是否已有 card_key）
3) 落事实：`cards_index + card_fields_eav + (card_rows/row_fields_eav) + blobs_index`
4) 取锁 + 分配 y（meta.dashboard_next_row）
5) 渲染 dashboard 块（批量写 range + 合并单元格 + 样式）
6) 更新 meta.next_row
7) 返回 (y,height)

---

## 9) 失败降级与重试（必须）

### 9.1 不允许的失败模式
- 写表失败导致 TG 主链路失败（禁止）
- dashboard 渲染失败导致事实也丢（禁止）

### 9.2 允许的失败模式（可恢复）
- dashboard 渲染失败，但事实已落：后续可 `force_render` 重画
- raw 太大写不进单元格：落 blob，表内存引用

---

## 10) 可观测性（验收必需）

服务端：
- outbox backlog size、flush 成功率、p95 延迟、重试次数、最后错误

Webhook：
- QPS、成功率、锁等待时间、写入耗时、渲染耗时

---

## 11) 迭代计划（MVP → 完整）

### Phase 0（对齐契约）
- 固化 `card_type` 列表、schema_version、dashboard 固定列区间与最大列策略

### Phase 1（MVP：先全量落事实）
- Webhook：写 `cards_index + card_fields_eav + blobs_index`
- dashboard 可先只写 title/update（验证链路）

### Phase 2（表格型卡片明细化）
- 补 `card_rows + row_fields_eav`
- 让 Sheets 透视表/筛选跑起来

### Phase 3（完整 dashboard 渲染）
- x,y 块渲染（表头 + 明细 + footer + 样式）
- 加入 `rebuild_dashboard(from_ts,to_ts)` 运维能力

---

## 12) 验收标准（Acceptance Criteria）
1) 任意卡片在 60 秒内可出现在 Sheets：至少 `cards_index` + `card_fields_eav` 落盘
2) 无遗漏可验证：raw_text / raw_json 可由 `blobs_index` 引用找回，hash 校验一致
3) 幂等可验证：同一卡片重复投递 10 次，事实表不重复，dashboard 不重复
4) 失败不阻塞可验证：断网期间 TG 正常发消息；恢复后 outbox 自动补写
5) dashboard 可重建：清空 dashboard 后能从事实表重放恢复

---

## 13) 需要你拍板的 4 个决策（会影响实现细节）
1) `dashboard` 固定列区间：用哪段（例如 N..Z）？
2) “超宽字段”策略：拆块（推荐）还是折行/截断？
3) Blob 存储：Drive 还是对象存储？（Drive 最快落地）
4) 是否需要“按 symbol 子表”（BTCUSDT）？（建议做派生视图，不强制每币建 sheet）

