from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Settings:
    raw: dict[str, Any]

    @property
    def config_version(self) -> str:
        return str(self.raw["config_version"])

    @property
    def strategy_version(self) -> str:
        return str(self.raw["strategy_version"])

    @property
    def lookback(self) -> str:
        return str(self.raw["lookback"])

    @property
    def cache_dir(self) -> Path:
        return Path(self.raw["cache_dir"]).resolve()

    @property
    def artifact_dir(self) -> Path:
        return Path(self.raw["artifact_dir"]).resolve()

    @property
    def indices(self) -> dict[str, str]:
        return dict(self.raw["indices"])

    @property
    def thresholds(self) -> dict[str, Any]:
        return dict(self.raw["thresholds"])

    @property
    def score_weights(self) -> dict[str, float]:
        return dict(self.raw["score_weights"])

    @property
    def trade_idea(self) -> dict[str, Any]:
        return dict(self.raw["trade_idea"])

    @property
    def backtest(self) -> dict[str, Any]:
        return dict(self.raw["backtest"])

    @property
    def universes(self) -> dict[str, Any]:
        return dict(self.raw.get("universes", {}))

    @property
    def forward_horizons(self) -> tuple[int, ...]:
        return tuple(int(x) for x in self.raw["forward_horizons"])


def load_settings(path: str | Path) -> Settings:
    config_path = Path(path)
    raw = json.loads(config_path.read_text(encoding="utf-8"))
    settings = Settings(raw=raw)
    settings.cache_dir.mkdir(parents=True, exist_ok=True)
    settings.artifact_dir.mkdir(parents=True, exist_ok=True)
    return settings
