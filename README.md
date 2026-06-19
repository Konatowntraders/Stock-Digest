# 📊 Trading Discord Daily Digest

A daily market briefing bot that posts to Discord every weekday morning via webhook. Pulls broad market data from Yahoo Finance and generates an AI-written summary using Claude.

---

## What It Posts

- **AI Summary** — Claude-written 4–6 sentence market briefing
- **Broad Market** — SPY, QQQ, DIA, IWM + VIX + all 11 sector ETFs
- **Treasury Yields** — 30-Year Treasury yield (`^TYX`) with its daily move in basis points
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

The cron targets **6:23 AM Pacific**. It's set to fire at `13:23 UTC` = `6:23 AM PDT` (summer). During winter (PST), change it to `14:23 UTC` to keep the same local time.

⚠️ **GitHub-scheduled workflows are best-effort and often run 5–30 minutes late** (queues are busiest at the top of the hour). That's why delivery time drifts. We schedule at `:50` rather than on the hour to minimize the drift, but exact timing isn't guaranteed by GitHub. If you need precise, reliable timing, trigger the workflow from an external scheduler (e.g. cron-job.org) via the [`workflow_dispatch` API](https://docs.github.com/en/rest/actions/workflows#create-a-workflow-dispatch-event) instead of relying on `schedule`.

---

## Stack

- `yfinance` — market data (free, no API key)
- `anthropic` — Claude AI summary
- `requests` — Discord webhook POST
- GitHub Actions — free scheduling
