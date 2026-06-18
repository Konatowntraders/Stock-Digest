# 📊 Trading Discord Daily Digest

A daily market briefing bot that posts to Discord every weekday morning via webhook. Pulls broad market data from Yahoo Finance and generates an AI-written summary using Claude.

---

## What It Posts

- **AI Summary** — Claude-written 4–6 sentence market briefing
- **Broad Market** — SPY, QQQ, DIA, IWM + VIX + all 11 sector ETFs
- **Top Movers** — Top 5 gainers and losers from S&P 500 sample
- **Watchlist** — Your custom tracked tickers

---

## Setup

### 1. Fork / Clone this repo to your GitHub account

### 2. Create a Discord Webhook
- Go to your Discord server → channel settings → Integrations → Webhooks
- Create a new webhook, copy the URL

### 3. Add GitHub Secrets
Go to your repo → Settings → Secrets and variables → Actions → New repository secret

| Secret Name | Value |
|---|---|
| `DISCORD_WEBHOOK_URL` | Your Discord webhook URL |
| `ANTHROPIC_API_KEY` | Your Anthropic API key |

### 4. Enable GitHub Actions
- Go to the Actions tab in your repo
- Enable workflows if prompted

That's it — it runs automatically Mon–Fri at 6:30 AM Pacific.

---

## Customizing the Watchlist

Edit `watchlist.json` and add/remove tickers:

```json
{
  "watchlist": ["TSLA", "NVDA", "AMD", "AAPL", "MSFT"]
}
```

Commit and push — the next run will pick up the changes.

---

## Manual Run

Go to Actions → Daily Market Digest → Run workflow to trigger it immediately.

---

## Timing Note

The cron runs at `13:30 UTC` which is `6:30 AM PDT` (summer). During winter (PST), change it to `14:30 UTC` to keep 6:30 AM local time.

---

## Stack

- `yfinance` — market data (free, no API key)
- `anthropic` — Claude AI summary
- `requests` — Discord webhook POST
- GitHub Actions — free scheduling
