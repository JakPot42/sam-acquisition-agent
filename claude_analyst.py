"""
claude_analyst.py — uses the Anthropic API to analyze SAM.gov opportunities.

Sends the opportunity text to Claude and gets back a structured compliance
matrix: summary, requirements, eval criteria, compliance flags, and a
capability statement outline.
"""

from __future__ import annotations

import json
import re

import anthropic

from config import ANTHROPIC_API_KEY, CLAUDE_MAX_TOKENS, CLAUDE_MODEL

_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

_PROMPT = """\
You are a defense acquisition analyst helping a small business understand a \
government contract opportunity. Analyze the solicitation below and return a \
JSON object — nothing else, no markdown, just raw JSON.

SOLICITATION:
{opportunity_text}

Return exactly this JSON structure:
{{
  "summary": "2-3 sentence plain-English description of what is being bought and why",
  "agency": "contracting agency name",
  "estimated_value": "dollar amount or range if stated, else null",
  "period_of_performance": "duration or date range if stated, else null",
  "place_of_performance": "city/state or remote, if stated, else null",
  "clearance_required": "security clearance level if required (e.g. Secret, TS/SCI), else null",
  "cmmc_level": "CMMC level if stated (e.g. Level 2), else null",
  "set_aside": "small business set-aside type if any, else null",
  "key_requirements": [
    {{"requirement": "plain-language requirement text", "category": "Technical|Personnel|Compliance|Past Performance|Other"}}
  ],
  "evaluation_criteria": [
    {{"criterion": "evaluation criterion", "weight": "weight or relative importance if stated, else null"}}
  ],
  "compliance_flags": [
    {{"flag": "compliance concern or special requirement", "severity": "High|Medium|Low"}}
  ],
  "capability_statement_bullets": [
    "bullet point for a capability statement response to this specific opportunity"
  ],
  "bottom_line": "1-sentence go/no-go assessment for a small defense-focused company"
}}
"""


class AnalysisError(Exception):
    pass


def analyze_opportunity(opportunity_text: str) -> dict:
    """Send opportunity text to Claude and return structured analysis dict."""
    try:
        response = _client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=CLAUDE_MAX_TOKENS,
            messages=[{
                "role": "user",
                "content": _PROMPT.format(opportunity_text=opportunity_text),
            }],
        )
    except anthropic.APIError as exc:
        raise AnalysisError(f"Anthropic API error: {exc}") from exc

    raw = response.content[0].text.strip()

    # Strip markdown code fences if the model wrapped the JSON anyway
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)

    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise AnalysisError(f"Could not parse Claude response as JSON: {exc}\n\nRaw: {raw}") from exc
