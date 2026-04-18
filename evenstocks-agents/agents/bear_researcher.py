"""Bear Researcher — argues against investing. Focus on risks, red flags, and overvaluation."""

from .base import BaseAgent


class BearResearcher(BaseAgent):
    name = "bear"
    max_tokens = 1200

    def system_prompt(self) -> str:
        return (
            "You are a Bear Researcher at an Indian equity research firm. Your job is to build the "
            "strongest evidence-based case AGAINST buying this stock. You look for: deteriorating margins, "
            "rising debt, promoter exits/pledge increases, competitive threats, regulatory risks, "
            "and overvaluation. You challenge the bull's optimism with hard data. "
            "You are a skeptic by design — but fair. Be conversational, not a bullet-point list."
        )

    def user_prompt(self, context: dict) -> str:
        ticker = context.get("ticker", "UNKNOWN")
        reports = context.get("analyst_reports") or {}
        history = context.get("debate_history", "")
        bull_last = context.get("last_bull_argument", "")
        round_num = context.get("debate_round", 1)

        reports_text = "\n".join(
            f"### {k.upper()}\n{v}" for k, v in reports.items()
        )

        return f"""Stock: **{ticker}** (Indian equity).

## Analyst reports
{reports_text}

## Debate so far
{history}

## Last argument from Bull
{bull_last}

## Your task (round {round_num})
{"Open with your bear case." if round_num == 1 else "Counter the Bull's latest argument with specific data, then present new concerns."}

Keep under 250 words. Cite specific numbers. Be direct and conversational — engage with the Bull's claims, don't just list risks."""


class ResearchManager(BaseAgent):
    """Synthesizes bull/bear debate into a balanced research view + conviction tilt."""

    name = "research_manager"
    max_tokens = 800

    def system_prompt(self) -> str:
        return (
            "You are the Head of Research at an Indian brokerage. You weigh the bull and bear cases and "
            "deliver a balanced research view with a conviction tilt. You are analytical, not argumentative. "
            "Your job is not to pick a winner — it's to say what's *more likely true* based on evidence."
        )

    def user_prompt(self, context: dict) -> str:
        ticker = context.get("ticker", "UNKNOWN")
        bull_history = context.get("bull_history", "")
        bear_history = context.get("bear_history", "")

        return f"""Synthesize the Bull vs Bear debate on Indian stock **{ticker}**.

## Bull arguments
{bull_history}

## Bear arguments
{bear_history}

## Required output (markdown)

### Points of agreement
What both sides concede or agree on.

### Key disagreement
The core point where they differ. Which side's evidence is stronger — and why?

### Balanced research view
A 2-3 sentence synthesis.

### Conviction tilt
One of: **Strong Bull / Bull Lean / Neutral / Bear Lean / Strong Bear**

Keep under 200 words."""
