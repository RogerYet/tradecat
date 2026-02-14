"""core.* 维表解析与注册（最小可用、可幂等）。

目标（说人话）：
- 事实表使用 (venue_id, instrument_id) 作为短主键，但采集侧天然拿到的是 (exchange, symbol)；
- 这里提供一个“最小且可重复执行”的映射层：
  - 确保 core.venue 存在对应 venue_code
  - 确保 core.instrument 存在对应 instrument
  - 确保 core.symbol_map 存在 (venue_id, symbol) -> instrument_id 的当前映射

约束与取舍：
- 不引入额外 schema/table；只使用既有 core.*（见 008_multi_market_core_and_storage.sql）
- 不试图一次性做完“金融工具规范化”（那会变复杂）；先保证写库可落地且可追溯。
"""

from __future__ import annotations

import logging
from typing import Optional, Tuple

import psycopg

logger = logging.getLogger(__name__)

KNOWN_QUOTES = ("USDT", "USDC", "BUSD", "USD", "TUSD", "FDUSD")


def _split_base_quote(symbol: str) -> Tuple[Optional[str], Optional[str]]:
    """尽力从 Binance 原生 symbol 推断 base/quote。

说明：
- 对于 BTCUSDT / ETHUSDT 等可稳定解析。
- 对于交割合约/复杂符号（含 '_' 或特殊后缀）无法保证正确，返回 (None, None)。
"""

    sym = str(symbol).upper().strip()
    if not sym:
        return None, None

    # 交割合约常见形态：BTCUSDT_240329（先取 '_' 前）
    main = sym.split("_", 1)[0]
    for quote in KNOWN_QUOTES:
        if main.endswith(quote) and len(main) > len(quote):
            return main[: -len(quote)], quote
    return None, None


def _infer_instrument_type(symbol: str, *, product: str) -> str:
    """用最小规则推断 instrument_type（只用于 core.instrument 的描述字段）。"""

    sym = str(symbol).upper()
    if "_" in sym:
        return "future"
    if product in {"futures_um", "futures_cm"}:
        return "perp"
    return "unknown"


class CoreRegistry:
    """core 维表的最小注册器（带本地缓存）。"""

    def __init__(self, conn: psycopg.Connection):
        self._conn = conn
        self._venue_id_cache: dict[str, int] = {}
        self._instrument_id_cache: dict[tuple[int, str], int] = {}

    def get_or_create_venue_id(
        self,
        venue_code: str,
        *,
        venue_name: Optional[str] = None,
        timezone: str = "UTC",
        cursor: Optional[psycopg.Cursor] = None,
    ) -> int:
        code = str(venue_code).strip().lower()
        if not code:
            raise ValueError("venue_code 不能为空")
        if code in self._venue_id_cache:
            return int(self._venue_id_cache[code])

        sql = """
        INSERT INTO core.venue (venue_code, venue_name, timezone)
        VALUES (%s, %s, %s)
        ON CONFLICT (venue_code) DO UPDATE
        SET venue_name = EXCLUDED.venue_name,
            timezone  = EXCLUDED.timezone
        RETURNING venue_id
        """

        name = (venue_name or code).strip()
        cur = cursor or self._conn.cursor()
        try:
            cur.execute(sql, (code, name, str(timezone)))
            row = cur.fetchone()
            if not row:
                raise RuntimeError(f"创建/获取 venue_id 失败: {code}")
            venue_id = int(row[0])
        finally:
            if cursor is None:
                cur.close()

        self._venue_id_cache[code] = venue_id
        return venue_id

    def get_or_create_instrument_id(
        self,
        *,
        venue_id: int,
        venue_code: str,
        symbol: str,
        product: str,
        cursor: Optional[psycopg.Cursor] = None,
    ) -> int:
        if venue_id <= 0:
            raise ValueError("venue_id 必须 > 0")
        sym = str(symbol).upper().strip()
        if not sym:
            raise ValueError("symbol 不能为空")

        cache_key = (int(venue_id), sym)
        if cache_key in self._instrument_id_cache:
            return int(self._instrument_id_cache[cache_key])

        cur = cursor or self._conn.cursor()
        try:
            # 1) 先看当前映射（避免重复造 instrument）
            cur.execute(
                """
                SELECT instrument_id
                FROM core.symbol_map
                WHERE venue_id = %s AND symbol = %s AND effective_to IS NULL
                ORDER BY effective_from DESC
                LIMIT 1
                """,
                (int(venue_id), sym),
            )
            row = cur.fetchone()
            if row:
                instrument_id = int(row[0])
                self._instrument_id_cache[cache_key] = instrument_id
                return instrument_id

            # 2) 不存在则创建 instrument + symbol_map
            base, quote = _split_base_quote(sym)
            instrument_type = _infer_instrument_type(sym, product=product)

            cur.execute(
                """
                INSERT INTO core.instrument (asset_class, instrument_type, base_currency, quote_currency, meta)
                VALUES (
                  'crypto',
                  %s,
                  %s,
                  %s,
                  jsonb_build_object(
                    'source', 'binance_vision',
                    'venue_code', %s,
                    'symbol', %s,
                    'product', %s
                  )
                )
                RETURNING instrument_id
                """,
                (instrument_type, base, quote, str(venue_code).lower(), sym, str(product)),
            )
            inst_row = cur.fetchone()
            if not inst_row:
                raise RuntimeError(f"创建 instrument 失败: venue={venue_code} symbol={sym}")
            instrument_id = int(inst_row[0])

            cur.execute(
                """
                INSERT INTO core.symbol_map (venue_id, symbol, instrument_id, effective_from, effective_to, meta)
                VALUES (
                  %s,
                  %s,
                  %s,
                  NOW(),
                  NULL,
                  jsonb_build_object('source','auto','created_by','binance-vision-service')
                )
                """,
                (int(venue_id), sym, int(instrument_id)),
            )
        finally:
            if cursor is None:
                cur.close()

        self._instrument_id_cache[cache_key] = instrument_id
        logger.info("core.symbol_map 新增映射: venue=%s(%d) symbol=%s -> instrument_id=%d", venue_code, venue_id, sym, instrument_id)
        return instrument_id

    def resolve_venue_and_instrument_id(
        self,
        *,
        venue_code: str,
        symbol: str,
        product: str,
        cursor: Optional[psycopg.Cursor] = None,
    ) -> tuple[int, int]:
        vid = self.get_or_create_venue_id(venue_code, cursor=cursor)
        iid = self.get_or_create_instrument_id(
            venue_id=vid,
            venue_code=venue_code,
            symbol=symbol,
            product=product,
            cursor=cursor,
        )
        return vid, iid


__all__ = ["CoreRegistry"]

