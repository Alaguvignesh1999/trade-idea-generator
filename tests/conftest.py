from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from trade_idea_generator.config import Settings, load_settings


@pytest.fixture()
def settings(tmp_path: Path) -> Settings:
    base = load_settings("configs/default.json")
    raw = dict(base.raw)
    raw["cache_dir"] = str(tmp_path / "cache")
    raw["artifact_dir"] = str(tmp_path / "artifacts")
    Path(raw["cache_dir"]).mkdir(parents=True, exist_ok=True)
    Path(raw["artifact_dir"]).mkdir(parents=True, exist_ok=True)
    return Settings(raw=raw)


@pytest.fixture()
def synthetic_close() -> pd.Series:
    idx = pd.date_range("2024-01-01", periods=320, freq="B")
    trend = np.linspace(100, 145, len(idx))
    wave = np.sin(np.linspace(0, 10, len(idx))) * 2.5
    return pd.Series(trend + wave, index=idx, name="TEST")


@pytest.fixture()
def synthetic_members(synthetic_close: pd.Series) -> pd.DataFrame:
    members = {}
    for i in range(12):
        members[f"T{i:02d}"] = synthetic_close * (1 + i * 0.01)
    return pd.DataFrame(members, index=synthetic_close.index)
