"""
tests/test_analyst.py — unit tests for the Claude analyst JSON parser.

These tests do NOT call the Anthropic API. They verify the parsing and
error-handling logic in claude_analyst.py using synthetic model responses.
"""

import json
import pytest
from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mock_response(text: str):
    """Build a minimal mock of the Anthropic messages response."""
    content_block = MagicMock()
    content_block.text = text
    response = MagicMock()
    response.content = [content_block]
    return response


VALID_ANALYSIS = {
    "summary": "Test summary.",
    "agency": "Test Agency",
    "estimated_value": "$1M",
    "period_of_performance": "1 year",
    "place_of_performance": "Remote",
    "clearance_required": "Secret",
    "cmmc_level": "Level 2",
    "set_aside": "Small Business",
    "key_requirements": [
        {"requirement": "Python experience", "category": "Technical"}
    ],
    "evaluation_criteria": [
        {"criterion": "Technical", "weight": "60%"}
    ],
    "compliance_flags": [
        {"flag": "Secret clearance required", "severity": "High"}
    ],
    "capability_statement_bullets": [
        "Proven Python development team"
    ],
    "bottom_line": "Good fit for a cleared small business.",
}


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestAnalyzeOpportunity:

    def test_parses_clean_json(self):
        """Model returns raw JSON — should parse cleanly."""
        from claude_analyst import analyze_opportunity
        with patch("claude_analyst._client") as mock_client:
            mock_client.messages.create.return_value = _mock_response(
                json.dumps(VALID_ANALYSIS)
            )
            result = analyze_opportunity("some RFP text")
        assert result["summary"] == "Test summary."
        assert result["clearance_required"] == "Secret"
        assert len(result["key_requirements"]) == 1

    def test_strips_markdown_fences(self):
        """Model wraps JSON in ```json ... ``` — should strip fences and parse."""
        from claude_analyst import analyze_opportunity
        wrapped = f"```json\n{json.dumps(VALID_ANALYSIS)}\n```"
        with patch("claude_analyst._client") as mock_client:
            mock_client.messages.create.return_value = _mock_response(wrapped)
            result = analyze_opportunity("some RFP text")
        assert result["agency"] == "Test Agency"

    def test_strips_plain_code_fences(self):
        """Model wraps JSON in ``` ... ``` without language tag."""
        from claude_analyst import analyze_opportunity
        wrapped = f"```\n{json.dumps(VALID_ANALYSIS)}\n```"
        with patch("claude_analyst._client") as mock_client:
            mock_client.messages.create.return_value = _mock_response(wrapped)
            result = analyze_opportunity("some RFP text")
        assert result["cmmc_level"] == "Level 2"

    def test_raises_on_invalid_json(self):
        """Non-parseable response raises AnalysisError, not a raw exception."""
        from claude_analyst import AnalysisError, analyze_opportunity
        with patch("claude_analyst._client") as mock_client:
            mock_client.messages.create.return_value = _mock_response(
                "Sorry, I cannot analyze this."
            )
            with pytest.raises(AnalysisError, match="Could not parse"):
                analyze_opportunity("some RFP text")

    def test_raises_on_api_error(self):
        """Anthropic API errors are wrapped in AnalysisError."""
        import anthropic
        from claude_analyst import AnalysisError, analyze_opportunity
        with patch("claude_analyst._client") as mock_client:
            mock_client.messages.create.side_effect = anthropic.APIConnectionError(
                request=MagicMock()
            )
            with pytest.raises(AnalysisError, match="Anthropic API error"):
                analyze_opportunity("some RFP text")

    def test_null_fields_accepted(self):
        """Analysis with null optional fields should parse without error."""
        from claude_analyst import analyze_opportunity
        sparse = {**VALID_ANALYSIS, "clearance_required": None, "cmmc_level": None,
                  "estimated_value": None}
        with patch("claude_analyst._client") as mock_client:
            mock_client.messages.create.return_value = _mock_response(
                json.dumps(sparse)
            )
            result = analyze_opportunity("minimal RFP")
        assert result["clearance_required"] is None
        assert result["cmmc_level"] is None


class TestSAMClient:

    def test_date_range_format(self):
        """_date_range returns MM/DD/YYYY strings within a 90-day window."""
        import datetime
        from sam_client import _date_range
        posted_from, posted_to = _date_range(90)
        fmt = "%m/%d/%Y"
        d_from = datetime.datetime.strptime(posted_from, fmt).date()
        d_to = datetime.datetime.strptime(posted_to, fmt).date()
        delta = (d_to - d_from).days
        assert delta == 90

    def test_date_range_to_is_today(self):
        """postedTo should be today."""
        import datetime
        from sam_client import _date_range
        _, posted_to = _date_range(30)
        today = datetime.date.today().strftime("%m/%d/%Y")
        assert posted_to == today

    def test_friendly_429_error(self):
        """HTTP 429 from SAM.gov produces a human-readable SAMAPIError."""
        import httpx
        from sam_client import SAMAPIError, search_opportunities
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.text = '{"code":"900804","message":"throttled"}'
        with patch("sam_client.httpx.get") as mock_get:
            mock_get.side_effect = httpx.HTTPStatusError(
                "429", request=MagicMock(), response=mock_response
            )
            with pytest.raises(SAMAPIError, match="quota"):
                search_opportunities("test query")

    def test_friendly_timeout_error(self):
        """httpx.TimeoutException produces a human-readable SAMAPIError."""
        import httpx
        from sam_client import SAMAPIError, search_opportunities
        with patch("sam_client.httpx.get") as mock_get:
            mock_get.side_effect = httpx.TimeoutException("timed out")
            with pytest.raises(SAMAPIError, match="timed out"):
                search_opportunities("test query")

    def test_build_opportunity_text_includes_title(self):
        """build_opportunity_text flattens key fields into a readable block."""
        from sam_client import build_opportunity_text
        opp = {
            "title": "Test Contract",
            "solicitationNumber": "ABC-123",
            "naicsCode": "541511",
            "description": "Do some software work.",
        }
        text = build_opportunity_text(opp)
        assert "Test Contract" in text
        assert "ABC-123" in text
        assert "541511" in text
        assert "Do some software work." in text
