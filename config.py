"""
config.py — central configuration for the SAM.gov Acquisition Intelligence Agent.
All API endpoints, model choices, and UI settings live here.
"""

from __future__ import annotations

import os
from dotenv import load_dotenv

load_dotenv()

# --- API keys (loaded from .env) ---
SAM_API_KEY = os.environ.get("SAM_API_KEY", "")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

# --- SAM.gov API ---
SAM_BASE_URL = "https://api.sam.gov/opportunities/v2/search"
SAM_DEFAULT_LIMIT = 10

# --- Claude model ---
# Haiku is cost-efficient for RFP analysis (~$0.01 per analysis).
CLAUDE_MODEL = "claude-haiku-4-5-20251001"
CLAUDE_MAX_TOKENS = 2048

# --- App UI ---
APP_TITLE = "SAM.gov Acquisition Intelligence Agent"
DEMO_MODE = True
DEMO_BANNER = "DEMONSTRATION ONLY — SYNTHETIC ANALYSIS — NOT FOR PROPOSAL SUBMISSION"

# --- Database ---
DATABASE_URL = "sqlite:///./sam_agent.db"
