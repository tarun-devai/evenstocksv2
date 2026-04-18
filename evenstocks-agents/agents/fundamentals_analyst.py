"""Fundamentals Analyst — reads Screener data and evaluates company financials."""

import json

from .base import BaseAgent


class FundamentalsAnalyst(BaseAgent):
    name = "fundamentals"

    def system_prompt(self) -> str:
        return (
            "You are a senior equity research analyst at an Indian brokerage with 20 years of experience "
            "analyzing Indian listed companies. You focus on fundamentals: revenue growth, operating margins, "
            "ROE, ROCE, debt levels, cash flow quality, and promoter holding trends. "
            "You think in INR crores, understand Indian accounting standards, and flag earnings manipulation red flags. "
            "Be direct, quantitative, and avoid generic statements. Every claim must reference a specific number."
        )

    def user_prompt(self, context: dict) -> str:
        ticker = context.get("ticker", "UNKNOWN")
        company_info = context.get("company_info") or {}
        financial_tables = context.get("financial_tables") or {}

        info_json = json.dumps(company_info, default=str)[:6000]
        tables_json = json.dumps(financial_tables, default=str)[:6000]

        return f"""Analyze the fundamentals of Indian stock **{ticker}**.

## Company info (from Screener.in)
{info_json}

## Financial tables
{tables_json}

## Required output (markdown)

### Business overview
1-2 lines on what the company does and its market position.

### Growth quality
- Revenue CAGR (3y, 5y): value + commentary
- PAT CAGR (3y, 5y): value + commentary
- Is growth consistent or lumpy?

### Margin profile
- Operating margin trend
- Net profit margin trend
- Return ratios (ROE, ROCE) vs industry

### Balance sheet health
- Debt/Equity
- Interest coverage
- Working capital cycle (if visible)
- Promoter pledge (if any — flag as CRITICAL)

### Red flags
List 0-5 red flags with numbers. If none, say "None detected."

### Verdict
One of: **Strong Fundamentals / Solid / Mixed / Weak / Deteriorating**

Keep response under 400 words. Use bullets and numbers — no fluff."""
