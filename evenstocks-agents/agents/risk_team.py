"""Risk Team — 3 risk analysts (aggressive, conservative, neutral) view the same data differently."""

from .base import BaseAgent


class _RiskAgent(BaseAgent):
    max_tokens = 800
    stance: str = "neutral"

    def stance_description(self) -> str:
        raise NotImplementedError

    def system_prompt(self) -> str:
        return (
            f"You are a {self.stance.upper()} Risk Analyst at an Indian portfolio management firm. "
            f"{self.stance_description()} "
            "You interpret the same data through your stance. You debate other risk analysts "
            "and highlight what they may be missing. Be direct and numerical."
        )

    def user_prompt(self, context: dict) -> str:
        ticker = context.get("ticker", "UNKNOWN")
        reports = context.get("analyst_reports") or {}
        research_view = context.get("research_view", "")

        reports_text = "\n".join(f"### {k.upper()}\n{v}" for k, v in reports.items())

        return f"""Stock: **{ticker}** (Indian equity).

## Analyst reports
{reports_text}

## Research team synthesis
{research_view}

## Your task
Give the {self.stance.upper()} risk view. Structure:

### Risk posture
Your core thesis in 1 sentence.

### Position sizing (out of 100% of investable capital)
- Max position size you'd allow: X%
- Recommended starting position: Y%

### Stop-loss philosophy
Where would you cut losses?

### What others are missing
1-2 things the other risk views underweight.

Keep under 180 words."""


class AggressiveRiskAnalyst(_RiskAgent):
    name = "risk_aggressive"
    stance = "aggressive"

    def stance_description(self) -> str:
        return (
            "You champion high-reward, high-risk opportunities. You see where caution becomes cost. "
            "You emphasize upside potential, growth runway, and the risk of underexposure in a moving stock."
        )


class ConservativeRiskAnalyst(_RiskAgent):
    name = "risk_conservative"
    stance = "conservative"

    def stance_description(self) -> str:
        return (
            "You prioritize capital preservation above all. You flag tail risks, liquidity issues, "
            "drawdown scenarios, and correlation with other holdings. You say no when in doubt."
        )


class NeutralRiskAnalyst(_RiskAgent):
    name = "risk_neutral"
    stance = "neutral"

    def stance_description(self) -> str:
        return (
            "You take the middle path — balance upside and downside. You look for asymmetry: "
            "scenarios where the risk-reward is skewed, regardless of direction."
        )


class RiskManager(BaseAgent):
    """Synthesizes 3 risk views into a final risk rating + sizing recommendation."""

    name = "risk_manager"
    max_tokens = 700

    def system_prompt(self) -> str:
        return (
            "You are the Chief Risk Officer at an Indian PMS. You read the 3 risk analysts' views and "
            "issue a final risk rating and position-sizing recommendation. You are decisive."
        )

    def user_prompt(self, context: dict) -> str:
        ticker = context.get("ticker", "UNKNOWN")
        aggressive = context.get("risk_aggressive_view", "")
        conservative = context.get("risk_conservative_view", "")
        neutral = context.get("risk_neutral_view", "")

        return f"""Synthesize risk views for Indian stock **{ticker}**.

## Aggressive view
{aggressive}

## Conservative view
{conservative}

## Neutral view
{neutral}

## Required output (markdown)

### Final risk rating
One of: **Low / Moderate / Elevated / High / Very High**

### Recommended position size
As % of investable capital (a single number or tight range).

### Stop-loss level
A concrete stop-loss philosophy (e.g., "8% below entry" or "below 52w moving average").

### Rationale
2-3 sentences.

Keep under 150 words."""
