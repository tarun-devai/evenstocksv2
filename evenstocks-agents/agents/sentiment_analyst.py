"""Sentiment Analyst — stub for Phase 1. Real impl in Phase 3 (US-C2: X/Twitter + Reddit)."""

from .base import BaseAgent
from config import settings


class SentimentAnalyst(BaseAgent):
    name = "sentiment"
    model = settings.QUICK_MODEL
    max_tokens = 600

    def system_prompt(self) -> str:
        return (
            "You are a retail sentiment analyst tracking Indian investor mood on X/Twitter, "
            "Reddit (r/IndianStocks, r/IndianStreetBets), and Telegram. "
            "You distinguish hype cycles from genuine conviction and flag euphoria as a contrarian signal."
        )

    def user_prompt(self, context: dict) -> str:
        ticker = context.get("ticker", "UNKNOWN")
        company_info = context.get("company_info") or {}
        sector = company_info.get("sector") or "General"

        return f"""**Phase 1 limitation:** X/Twitter/Reddit integrations are stubs (coming Phase 3).

Give a **sector-level retail sentiment read** for Indian stock **{ticker}** (sector: {sector}).

## Required output (markdown)

### Sector sentiment
One sentence on retail mood toward this sector.

### Likely retail positioning
- Are Indian retail investors typically bullish/bearish on this type of name?
- Any specific narrative driving attention?

### Contrarian signal
If retail is euphoric → caution flag. If retail is fearful → opportunity flag. Otherwise neutral.

### Verdict
One of: **Extreme Greed / Greedy / Neutral / Fearful / Extreme Fear**

**Disclaimer:** "Based on sector heuristics — live X/Reddit feed in Phase 3."

Keep under 150 words."""
