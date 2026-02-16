"""配置（骨架）。

目标：支持“两库共存”且最小改动。

约定：
- 默认从环境变量读取，避免引入新的配置系统。
- 为避免两套数据库混淆，binance-vision-service 优先使用 `BINANCE_VISION_DATABASE_URL`；
  若未设置，则回退到通用 `DATABASE_URL`（兼容旧用法）。
"""

from __future__ import annotations

from dataclasses import dataclass
import os


@dataclass(frozen=True)
class AppConfig:
    """应用配置（最小占位）。"""

    database_url: str = os.getenv("BINANCE_VISION_DATABASE_URL") or os.getenv("DATABASE_URL", "")
    binance_data_base: str = os.getenv("BINANCE_DATA_BASE", "https://data.binance.vision")


def load_config() -> AppConfig:
    return AppConfig()
