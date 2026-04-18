"""News Analyst — stub for Phase 1. Real implementation in Phase 3 (US-C1)."""

from .base import BaseAgent


class NewsAnalyst(BaseAgent):
    name = "news"
    max_tokens = 800

    def system_prompt(self) -> str:
        return (
            "You are a financial news analyst covering Indian markets. "
            "You synthesize news impact on stocks from Moneycontrol, Economic Times, Livemint, Business Standard, "
            "and BSE/NSE announcements. You distinguish noise from material events."
        )

    def user_prompt(self, context: dict) -> str:
        ticker = context.get("ticker", "UNKNOWN")
        company_info = context.get("company_info") or {}
        sector = company_info.get("sector") or company_info.get("industry") or "Unknown"

        return f"""**Phase 1 limitation:** real-time news integration is not yet wired in (coming in Phase 3).

For now, give a **generic sector-level news context** for Indian stock **{ticker}** in sector **{sector}**.

## Required output (markdown)

### Sector news backdrop
2-3 bullets on what's typically in the news for this sector right now (based on your knowledge).

### Likely catalysts to watch
- Next 7 days
- Next quarter

### Risk events
Events that could move the stock significantly.

### Verdict
One of: **Tailwinds / Neutral / Headwinds**

**Disclaimer to include at the top:** "Based on sector-level context only — live news feed integration coming in Phase 3."

Keep under 200 words."""
