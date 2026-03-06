# ACCEPTANCE：验收标准（可执行 + 可验证）

## A. Happy Path（主路径）

### A1：币种查询导出稳定，不再“看起来挂了”

- 操作：
  - 在 `services/consumption/sheets-service/` 下执行一次强制刷新（SA 模式）：
    ```bash
    cd services/consumption/sheets-service
    python -m src --once --force --write-mode sa --lang zh_CN
    ```
- 断言：
  - 进程退出码为 0
  - 日志（systemd 或 stdout）中不存在 `HttpError 400`（结构性错误）与 `Cannot delete all non-frozen` 语义

### A2：compact grid 与冻结行列不变量成立（避免结构性 400）

- 操作：读取一个币种查询 tab 的 gridProperties（只读）
  ```bash
  cd services/consumption/sheets-service
  python - <<'PY'
  import os, json
  from google.oauth2.service_account import Credentials
  from googleapiclient.discovery import build
  sid = os.environ["SHEETS_SPREADSHEET_ID"].strip()
  cred = os.environ["SHEETS_SA_CREDENTIALS_PATH"].strip() or os.environ["GOOGLE_APPLICATION_CREDENTIALS"].strip()
  tab = (os.environ.get("SHEETS_SYMBOL_TAB_PREFIX","币种查询_") or "币种查询_") + (os.environ.get("SYMBOLS_GROUP_main4","BTCUSDT").split(",")[0].strip().upper() or "BTCUSDT")
  scopes = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
  svc = build("sheets", "v4", credentials=Credentials.from_service_account_file(cred, scopes=scopes))
  ss = svc.spreadsheets().get(
      spreadsheetId=sid,
      fields="sheets.properties(sheetId,title,gridProperties(rowCount,columnCount,frozenRowCount,frozenColumnCount))",
  ).execute()
  gp = None
  for sh in ss.get("sheets", []):
      p = (sh.get("properties") or {})
      if p.get("title") == tab:
          gp = (p.get("gridProperties") or {})
          break
  assert gp, f"missing_tab:{tab}"
  rc, cc = int(gp.get("rowCount") or 0), int(gp.get("columnCount") or 0)
  fr, fc = int(gp.get("frozenRowCount") or 0), int(gp.get("frozenColumnCount") or 0)
  assert rc >= fr + 1, (rc, fr)
  assert cc >= fc + 1, (cc, fc)
  print(json.dumps({"tab": tab, "grid": gp}, ensure_ascii=False))
  PY
  ```
- 断言：
  - 输出 JSON 中满足：`rowCount >= frozenRowCount + 1` 且 `columnCount >= frozenColumnCount + 1`

### A3：表头样式“全量一致”（不残留旧版）

- 操作：浏览器打开任意币种查询 tab（例如 `币种查询_BTCUSDT`），观察冻结区（前 3 行、前 3 列）。
- 断言：
  - banner（若启用）为整行统一背景色，不出现分裂
  - meta+目录行（合并/视觉合并）为统一背景色
  - 表头行（`币种/字段/指标组/指标/周期列...`）背景色一致，不再出现 A3 与其它列不同色
  - 目录单元格为单行溢出显示（不自动换行），逗号分隔可点击跳转

## B. Edge Cases（至少 3 个边缘场景）

### B1：空/极小表（行列数接近冻结行列）

- 约束：当 `n_rows/n_cols` 很小（例如暂时只有 banner+meta+header，或某指标组为空）时
- 断言：导出依然不触发结构性 400；gridProperties 自动纠偏满足不变量（A2）

### B2：关闭 compact grid

- 操作：临时设置 `SHEETS_SYMBOL_QUERY_COMPACT_GRID=0`，执行 A1
- 断言：导出成功；且不出现“超出网格范围 clear 导致 400”

### B3：目录 RichText 链接的 UTF-16 startIndex 边界

- 约束：目录条目存在 emoji/前缀图标或条目数量多
- 断言：不出现 `TextFormatRun.startIndex` 相关 400；目录仍保留可点击跳转（允许退化为纯文本但必须可观测）

## C. Anti-Goals（禁止性准则）

- 不允许回退为“分隔符伪表格”（必须保持结构化表格）。
- 不允许隐藏网格线（`hideGridlines` 必须保持 `False`）。
- 不允许改变任何指标数值（只允许调整展示样式/冻结/网格属性/目录链接）。

