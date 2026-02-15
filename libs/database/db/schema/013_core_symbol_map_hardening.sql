-- 013_core_symbol_map_hardening.sql
--
-- 目标：
-- - 把 symbol_map 的“语义正确性”写死在数据库层，避免半年后出现脏映射才追查。
--
-- 背景（问题）：
-- - core.symbol_map 目前只有 PRIMARY KEY (venue_id, symbol, effective_from)。
-- - 这允许同一个 (venue_id, symbol) 同时存在多条 active（effective_to IS NULL）映射；
--   上层如果用 LIMIT 1 “挑一条”，只是掩盖问题，不是阻止问题。

CREATE SCHEMA IF NOT EXISTS core;

-- 用于 EXCLUDE 约束（= / &&）的 GIST 操作符族（避免手写 trigger）。
CREATE EXTENSION IF NOT EXISTS btree_gist;

-- 只允许每个 (venue_id, symbol) 同时存在 1 条 active 映射（effective_to IS NULL）。
CREATE UNIQUE INDEX IF NOT EXISTS uq_core_symbol_map_active
ON core.symbol_map (venue_id, symbol)
WHERE effective_to IS NULL;

-- 可选但强烈建议：只允许每个 (venue_id, instrument_id) 同时存在 1 条 active symbol。
-- 否则“按 instrument_id 反查 symbol”的 readable view 可能出现一对多，只能靠 LIMIT 1 兜底（掩盖脏数据）。
CREATE UNIQUE INDEX IF NOT EXISTS uq_core_symbol_map_active_instrument
ON core.symbol_map (venue_id, instrument_id)
WHERE effective_to IS NULL;

-- 有效期窗口必须自洽：要么永久有效（effective_to IS NULL），要么 effective_to > effective_from。
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'chk_core_symbol_map_effective_window'
          AND conrelid = 'core.symbol_map'::regclass
    ) THEN
        EXECUTE
            'ALTER TABLE core.symbol_map ' ||
            'ADD CONSTRAINT chk_core_symbol_map_effective_window ' ||
            'CHECK (effective_to IS NULL OR effective_to > effective_from)';
    END IF;
END
$$;

-- 防止“历史窗口重叠”（真正的 as-of 语义底座）：
-- - 同一 (venue_id, symbol) 在任意时间只能映射到 1 个 instrument_id
-- - 同一 (venue_id, instrument_id) 在任意时间只能对应 1 个 symbol
-- 说明：
-- - 我们使用 [effective_from, effective_to) 半开区间；effective_to=NULL 视为 infinity
-- - 若未来要“换映射”，必须先把旧行 effective_to 关掉，再插入新行，否则会被硬约束拦住
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'excl_core_symbol_map_symbol_window'
          AND conrelid = 'core.symbol_map'::regclass
    ) THEN
        EXECUTE $sql$
            ALTER TABLE core.symbol_map
            ADD CONSTRAINT excl_core_symbol_map_symbol_window
            EXCLUDE USING gist (
              venue_id WITH =,
              symbol WITH =,
              tstzrange(
                effective_from,
                COALESCE(effective_to, 'infinity'::timestamptz),
                '[)'
              ) WITH &&
            )
        $sql$;
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'excl_core_symbol_map_instrument_window'
          AND conrelid = 'core.symbol_map'::regclass
    ) THEN
        EXECUTE $sql$
            ALTER TABLE core.symbol_map
            ADD CONSTRAINT excl_core_symbol_map_instrument_window
            EXCLUDE USING gist (
              venue_id WITH =,
              instrument_id WITH =,
              tstzrange(
                effective_from,
                COALESCE(effective_to, 'infinity'::timestamptz),
                '[)'
              ) WITH &&
            )
        $sql$;
    END IF;
END
$$;
