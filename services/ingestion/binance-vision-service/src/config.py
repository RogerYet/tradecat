"""配置（骨架）。

# 约定：
# - 运行时配置由顶层 `config/.env` 提供（start.sh 会进行安全加载）。
# - Python 侧直接从环境变量读取，避免引入新的配置系统。
"""

from __future__ import annotations

from dataclasses import dataclass
import os


@dataclass(frozen=True)
class AppConfig:
    """应用配置（最小占位）。"""

    database_url: str = os.getenv("DATABASE_URL", "")
    binance_data_base: str = os.getenv("BINANCE_DATA_BASE", "https://data.binance.vision")


def load_config() -> AppConfig:
    return AppConfig()
