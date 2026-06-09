# SAM.gov Acquisition Intelligence Agent

An AI-powered web application that searches the US government's public
contracting database, retrieves active solicitations, and uses Claude AI
to produce a structured **compliance matrix** — requirements list, evaluation
criteria breakdown, compliance flags (CMMC, clearance level, set-aside), and
a tailored capability statement outline.

Built for small defense-focused companies that currently spend 20+ hours per
bid doing this manually.

**Live demo:** https://sam-acquisition-agent.onrender.com

> ⚠️ **Demonstration project.** AI analysis is illustrative and must be verified
> against the official solicitation on SAM.gov before submitting any proposal.

---

## Live demo

**[▶ Launch demo →](https://sam-acquisition-agent.onrender.com)**
*(free Render tier — first load may take ~30 s to wake from sleep)*

---

## What it demonstrates

- **External API integration** — queries the SAM.gov Opportunities API (public US government data) for real, live solicitations.
- **Claude AI agent** — sends RFP text to Claude and extracts structured JSON: requirements, eval criteria, compliance flags, capability bullets, go/no-go assessment.
- **Robust JSON extraction** — handles model variance (markdown fences, minor formatting drift) without failing silently.
- **SQLite caching** — previously fetched opportunities and analyses are stored locally; re-analyzing is cheap but doesn't require a redundant API call.
- **Defense domain knowledge** — compliance flags surface CMMC levels, clearance requirements, set-aside types, and other acquisition-specific concerns automatically.

## Features

| Feature | Detail |
|---|---|
| Keyword search | Queries SAM.gov live for active solicitations |
| Opportunity detail | Full description, dates, NAICS, set-aside type |
| AI compliance matrix | Requirements list · eval criteria · compliance flags |
| Capability statement | Tailored bullet-point outline per solicitation |
| Go / No-go | One-sentence bottom-line assessment |
| Analysis history | All past analyses stored and browsable |

## Tech stack

FastAPI · SQLAlchemy 2.0 · Pydantic v2 · Jinja2 · httpx · Anthropic Python SDK · SQLite · vanilla CSS (no CDN)

## Architecture

```
config.py           API keys, model choice, constants
sam_client.py       SAM.gov Opportunities API wrapper
claude_analyst.py   Anthropic API call + JSON extraction
models.py           SQLAlchemy ORM (Opportunity, Analysis)
database.py         Engine + session plumbing
main.py             FastAPI routes
templates/          Jinja2 HTML (search, results, opportunity, analysis, history)
static/css/         Local stylesheet
```

The SAM client and Claude analyst are fully decoupled from the web layer —
`sam_client.py` and `claude_analyst.py` can be called and tested independently.

## Running it

**Windows (easiest):** double-click `START_HERE.bat`.

**Manual:**
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Copy `.env.example` to `.env` and fill in your API keys before starting.

## Environment variables

```
SAM_API_KEY=        # Free from api.data.gov
ANTHROPIC_API_KEY=  # From console.anthropic.com
```

## Design decisions

- **Haiku model for cost efficiency.** Each analysis costs ~$0.01 at Claude Haiku pricing. Swapping to a more capable model is a one-line change in `config.py`.
- **Structured JSON output with regex fallback.** The Claude prompt requests raw JSON; if the model wraps it in markdown code fences anyway, a regex strips them before parsing. This prevents a hard failure on minor model variance.
- **Caching fetched opportunities.** SAM.gov has rate limits. Storing the raw JSON locally means re-analyzing an opportunity doesn't re-hit the API.
- **`sync: false` for secrets in render.yaml.** API keys are marked as secrets in the Render config — they must be set manually in the Render dashboard, never committed to git.

## Honest limitations

- **Description-only analysis.** SAM.gov often attaches the full RFP as a PDF. This version analyzes the API description field only — a future version would download and parse attachments for much richer analysis.
- **No authentication.** The app has no login. For a real product, each user/company would need their own account.
- **SQLite is ephemeral on Render free tier.** Data resets on each deploy. Acceptable for a portfolio demo; a real deployment would use PostgreSQL.

## License

MIT (sample/educational project).
