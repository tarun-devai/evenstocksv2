"""Technical Analyst — price action, moving averages, momentum. Uses limited data available."""

import json

from .base import BaseAgent


class TechnicalAnalyst(BaseAgent):
    name = "technical"

    def system_prompt(self) -> str:
        return (
            "You are a technical analyst specializing in Indian equities on NSE/BSE. "
            "You analyze price action, trend strength, support/resistance, volume, and momentum. "
            "You use RSI, MACD, moving averages, and pivot points. "
            "You understand Indian market quirks: circuit limits, F&O expiry effects, gap-up/gap-down patterns. "
            "Be direct and price-level specific."
        )

    def user_prompt(self, context: dict) -> str:
        ticker = context.get("ticker", "UNKNOWN")
        company_info = context.get("company_info") or {}

        current_price = company_info.get("current_price")
        high_low = {
            "52w_high": company_info.get("high_price"),
            "52w_low": company_info.get("low_price"),
        }

        info_summary = {
            "current_price": current_price,
            "52w_range": high_low,
            "market_cap": company_info.get("market_cap"),
            "face_value": company_info.get("face_value"),
            "book_value": company_info.get("book_value"),
            "dividend_yield": company_info.get("dividend_yield"),
        }

        return f"""Analyze the price action for Indian stock **{ticker}**.

## Price snapshot
{json.dumps(info_summary, default=str)}

## Required output (markdown)

### Trend
- Current trend: **Uptrend / Downtrend / Sideways**
- Position within 52-week range (%)

### Key levels
- Immediate support
- Immediate resistance
- Major support (if breaks, deeper fall)
- Major resistance (if breaks, rally target)

### Momentum read
Based on price vs 52w range: is it overbought, oversold, or neutral?

### Trade setup
- Entry zone
- Stop-loss
- Target 1
- Target 2 (stretch)

### Verdict
One of: **Strong Buy / Buy / Hold / Sell / Strong Sell**

NOTE: You have only basic price data. State confidence level honestly (low/medium/high) based on data availability.
Keep under 300 words."""
