from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class TradeIdea:
    setup_key: str
    name: str
    direction: str
    conviction: float
    suitability: float
    thesis: str
    signal_reasons: list[str]
    entry: float
    stop: float
    target: float
    stretch_target: float
    time_horizon_days: int
    invalidation: str
    confidence_inputs: dict[str, float]
    historical_context: dict[str, float]
    backtest_rule: str
    status: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ActionBoardItem:
    symbol: str
    name: str
    sector: str
    direction: str
    conviction: float
    diversified_score: float
    setup_key: str
    rationale: str
    entry: float
    stop: float
    target: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class EntryPlan:
    layer: str
    item: str
    direction: str
    trigger_entry: float
    pullback_entry: float
    failure_level: float
    target: float
    execution_note: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Tripwire:
    name: str
    current_value: str
    threshold: str
    status: str
    risk: str
    response: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Snapshot:
    as_of: str
    market: str
    data_quality: dict[str, Any]
    regime: dict[str, Any]
    signal_scores: list[dict[str, Any]]
    trade_ideas: list[dict[str, Any]]
    action_board: list[dict[str, Any]]
    tripwires: list[dict[str, Any]]
    risk_budget: dict[str, Any]
    entry_plans: list[dict[str, Any]]
    metadata: dict[str, Any]
    research: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class BacktestResult:
    market: str
    strategy_version: str
    config_version: str
    test_window: dict[str, str]
    entry_rule: str
    exit_rule: str
    cost_assumptions: dict[str, float]
    summary_metrics: dict[str, float]
    setup_breakdowns: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
