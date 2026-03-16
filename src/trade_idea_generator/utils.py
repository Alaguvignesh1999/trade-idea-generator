from __future__ import annotations

import math
import re


def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, float(value)))


def safe_float(value: object, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        result = float(value)
        if math.isnan(result):
            return default
        return result
    except (TypeError, ValueError):
        return default


def slugify(text: str) -> str:
    normalized = text.replace("S&P", "SP")
    return re.sub(r"[^a-z0-9]+", "-", normalized.lower()).strip("-")


def parse_price_text(value: object) -> float:
    if value is None:
        return float("nan")
    match = re.search(r"[-+]?\d+(?:\.\d+)?", str(value).replace(",", ""))
    return float(match.group(0)) if match else float("nan")


def risk_reward(entry: float, stop: float, target: float, direction: str) -> float:
    if direction == "LONG":
        risk = entry - stop
        reward = target - entry
    else:
        risk = stop - entry
        reward = entry - target
    if risk <= 0:
        return float("nan")
    return reward / risk
