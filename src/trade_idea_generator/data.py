from __future__ import annotations

import time
from pathlib import Path
from typing import Any

import pandas as pd
import yfinance as yf

from .config import Settings


def _safe_name(text: str) -> str:
    return "".join(c if c.isalnum() or c in {"-", "_"} else "_" for c in text)


def _cache_file(settings: Settings, key: str) -> Path:
    return settings.cache_dir / f"{_safe_name(key)}.pkl"


def download_close(tickers: list[str], lookback: str) -> pd.DataFrame:
    data = yf.download(
        tickers=tickers,
        period=lookback,
        progress=False,
        group_by="column",
        threads=True,
        auto_adjust=False,
    )
    if data is None or len(data) == 0:
        return pd.DataFrame()
    if isinstance(data.columns, pd.MultiIndex):
        close = data["Close"].copy()
    else:
        close = data[["Close"]].rename(columns={"Close": tickers[0]})
    close = close.sort_index()
    close.columns = [str(col).strip() for col in close.columns]
    return close


def load_or_download_close(settings: Settings, tickers: list[str], cache_key: str) -> pd.DataFrame:
    path = _cache_file(settings, cache_key)
    if path.exists():
        cached = pd.read_pickle(path)
        if isinstance(cached, pd.DataFrame) and len(cached.columns):
            missing = [ticker for ticker in tickers if ticker not in cached.columns]
            if not missing:
                return cached.ffill()
            fresh = download_close(missing, settings.lookback)
            merged = pd.concat([cached, fresh], axis=1).sort_index()
            merged = merged.loc[:, ~merged.columns.duplicated()]
            merged.to_pickle(path)
            return merged.ffill()
    fresh = download_close(tickers, settings.lookback)
    fresh.to_pickle(path)
    return fresh.ffill()


def load_index_close(settings: Settings, market_name: str) -> pd.Series:
    ticker = settings.indices[market_name]
    prices = load_or_download_close(settings, [ticker], f"prices__{market_name}__index")
    if ticker not in prices.columns:
        return pd.Series(dtype=float, name=ticker)
    return prices[ticker].rename(ticker).ffill()


def load_constituents(settings: Settings, market_name: str) -> pd.DataFrame:
    universe = settings.universes.get(market_name)
    if not universe:
        return pd.DataFrame(columns=["Symbol", "Name", "Sector"])
    path = _cache_file(settings, f"constituents__{market_name}")
    if path.exists():
        return pd.read_pickle(path)
    constituents_source = universe.get("constituents_path") or universe["constituents_url"]
    table = pd.read_csv(constituents_source)
    rename_map = {
        universe.get("symbol_column", "Symbol"): "Symbol",
        universe.get("name_column", "Name"): "Name",
    }
    if universe.get("sector_column"):
        rename_map[universe["sector_column"]] = "Sector"
    table = table.rename(columns=rename_map)
    for column in ["Symbol", "Name", "Sector"]:
        if column not in table.columns:
            table[column] = ""
    table["Symbol"] = table["Symbol"].astype(str).str.replace(".", "-", regex=False)
    table = table[["Symbol", "Name", "Sector"]].drop_duplicates().reset_index(drop=True)
    path.parent.mkdir(parents=True, exist_ok=True)
    table.to_pickle(path)
    return table


def load_member_universe_close(settings: Settings, market_name: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    constituents = load_constituents(settings, market_name)
    if constituents.empty:
        return pd.DataFrame(), constituents
    max_members = int(settings.universes[market_name].get("max_members", len(constituents)))
    members = constituents.head(max_members).copy()
    prices = load_or_download_close(settings, members["Symbol"].tolist(), f"prices__{market_name}__members")
    if prices.empty:
        return pd.DataFrame(), members
    missing_ratio = prices.isna().mean()
    keep = missing_ratio[missing_ratio <= 0.08].index.tolist()
    cleaned = prices[keep].ffill()
    trimmed_members = members[members["Symbol"].isin(keep)].reset_index(drop=True)
    return cleaned, trimmed_members


def health_summary(close: pd.Series, members: pd.DataFrame, member_prices: pd.DataFrame) -> dict[str, Any]:
    return {
        "index_rows": int(len(close)),
        "index_empty": bool(len(close) == 0),
        "constituent_rows": int(len(members)),
        "member_price_columns": int(member_prices.shape[1]) if not member_prices.empty else 0,
        "member_coverage": float(member_prices.notna().iloc[-1].mean()) if not member_prices.empty else None,
        "generated_at_epoch": int(time.time()),
    }
