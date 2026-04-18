"""Bull Researcher — argues for investing in the stock. Uses all analyst reports."""

from .base import BaseAgent


class BullResearcher(BaseAgent):
    name = "bull"
    max_tokens = 1200

    def system_prompt(self) -> str:
        return (
            "You are a Bull Researcher at an Indian equity research firm. Your job is to build the "
            "strongest evidence-based case FOR buying this stock. You engage directly with bear arguments "
            "and refute them with specific data. You focus on: growth potential, competitive moat, "
            "industry tailwinds, positive catalysts, and undervaluation signals. "
            "You do NOT ignore risks — you contextualize them. Be conversational, not a bullet-point list."
        )

    def user_prompt(self, context: dict) -> str:
        ticker = context.get("ticker", "UNKNOWN")
        reports = context.get("analyst_reports") or {}
        history = context.get("debate_history", "")
        bear_last = context.get("last_bear_argument", "")
        round_num = context.get("debate_round", 1)

        reports_text = "\n".join(
            f"### {k.upper()}\n{v}" for k, v in reports.items()
        )

        history_block = (
            f"\n## Debate so far\n{history}\n"
            f"\n## Last argument from Bear\n{bear_last}\n"
        ) if history else ""

        task = (
            "Open the debate with your bull case."
            if round_num == 1
            else "Respond to the Bear's latest point, refute it specifically, and strengthen your case."
        )

        return f"""Stock: **{ticker}** (Indian equity).

## Analyst reports
{reports_text}
{history_block}
## Your task (round {round_num})
{task}

Keep under 250 words. Cite specific numbers from the analyst reports. Be direct and conversational."""
