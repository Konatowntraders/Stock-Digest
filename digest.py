import os
import json
import requests
import yfinance as yf
from datetime import datetime, date
import anthropic

# ── Config ────────────────────────────────────────────────────────────────────
DISCORD_WEBHOOK_URL = os.environ["DISCORD_WEBHOOK_URL"]
ANTHROPIC_API_KEY   = os.environ["ANTHROPIC_API_KEY"]

WATCHLIST_FILE = "watchlist.json"

BROAD_MARKET = {
    "Indices":  ["SPY", "QQQ", "DIA", "IWM"],
    "Volatility": ["^VIX"],
    "Sectors":  ["XLK", "XLE", "XLF", "XLV", "XLY", "XLP", "XLI", "XLB", "XLU", "XLRE", "XLC"],
}

SP500_SAMPLE = [
    "AAPL","MSFT","NVDA","GOOGL","AMZN","META","TSLA","BRK-B","JPM","UNH",
    "XOM","JNJ","V","PG","MA","HD","CVX","MRK","ABBV","PEP","KO","AVGO",
    "LLY","COST","WMT","BAC","MCD","CRM","TMO","ACN","CSCO","ABT","DHR",
    "TXN","NKE","ADBE","WFC","PM","NEE","RTX","AMGN","UPS","QCOM","INTU",
    "HON","IBM","CAT","GS","SPGI","BLK","SBUX","AMD","GILD","AXP","DE",
    "MMM","BA","C","MDLZ","ISRG","REGN","VRTX","ZTS","NOW","PANW","AMAT",
    "MU","ADI","KLAC","LRCX","SNPS","CDNS","FTNT","MRVL","ON","NXPI",
]

# ── Helpers ───────────────────────────────────────────────────────────────────

def load_watchlist():
    try:
        with open(WATCHLIST_FILE) as f:
            data = json.load(f)
            return data.get("watchlist", [])
    except FileNotFoundError:
        return []

VOLUME_SPIKE_THRESHOLD = 2.0  # flag if today's volume >= 2x the 3-month average

def fetch_quote(ticker: str) -> dict | None:
    try:
        t = yf.Ticker(ticker)
        info = t.fast_info
        prev  = info.previous_close or 0
        price = info.last_price      or 0
        if prev == 0:
            return None
        change_pct = ((price - prev) / prev) * 100

        avg_vol     = getattr(info, "three_month_average_volume", None)
        today_vol   = getattr(info, "last_volume", None)
        spike_ratio = round(today_vol / avg_vol, 2) if avg_vol and today_vol and avg_vol > 0 else None

        return {
            "ticker":      ticker,
            "price":       round(price, 2),
            "prev_close":  round(prev, 2),
            "change_pct":  round(change_pct, 2),
            "avg_volume":  avg_vol,
            "today_volume": today_vol,
            "spike_ratio": spike_ratio,
        }
    except Exception:
        return None

def detect_volume_spikes(quotes: list[dict], threshold: float = VOLUME_SPIKE_THRESHOLD) -> list[dict]:
    """Return quotes where today's volume is >= threshold x the 3-month average."""
    spikes = []
    for q in quotes:
        if q.get("spike_ratio") and q["spike_ratio"] >= threshold:
            spikes.append(q)
    spikes.sort(key=lambda x: x["spike_ratio"], reverse=True)
    return spikes

def fmt_spike(q: dict) -> str:
    direction = "📈" if q["change_pct"] >= 0 else "📉"
    return (
        f"⚡ **{q['ticker']}** {direction} {q['spike_ratio']}x avg vol | "
        f"${q['price']} ({q['change_pct']:+.2f}%)"
    )

def fetch_group(tickers: list[str]) -> list[dict]:
    results = []
    for t in tickers:
        q = fetch_quote(t)
        if q:
            results.append(q)
    return results

def get_top_movers(n=5) -> tuple[list, list]:
    quotes = []
    for ticker in SP500_SAMPLE:
        q = fetch_quote(ticker)
        if q:
            quotes.append(q)
    quotes.sort(key=lambda x: x["change_pct"])
    losers  = quotes[:n]
    gainers = quotes[-n:][::-1]
    return gainers, losers

def arrow(pct: float) -> str:
    return "🟢" if pct >= 0 else "🔴"

def fmt_quote(q: dict) -> str:
    return f"{arrow(q['change_pct'])} **{q['ticker']}** ${q['price']} ({q['change_pct']:+.2f}%)"

# ── Claude summary ────────────────────────────────────────────────────────────

def get_ai_summary(market_data: dict) -> str:
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    prompt = f"""You are a concise market analyst writing a morning briefing for active traders in a Discord server.

Here is today's market snapshot data:
{json.dumps(market_data, indent=2)}

Write a 4-6 sentence natural language summary covering:
- Overall market tone (risk-on/risk-off, bullish/bearish)
- Key sector themes
- Any standout movers worth watching
- One sentence on what traders should watch today

Keep it punchy, direct, no fluff. No bullet points — flowing prose only."""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=400,
        messages=[{"role": "user", "content": prompt}]
    )
    return message.content[0].text.strip()

# ── Discord embeds ────────────────────────────────────────────────────────────

def build_embeds(broad: dict, gainers: list, losers: list, watchlist_data: list, spikes: list, summary: str) -> list:
    today = datetime.now().strftime("%A, %B %d %Y")
    embeds = []

    # ── 1. AI Summary ──────────────────────────────────────────────────────────
    embeds.append({
        "title": f"📊 Daily Market Digest — {today}",
        "description": summary,
        "color": 0x2B2D31,
        "footer": {"text": "Data via Yahoo Finance • AI summary via Claude"}
    })

    # ── 2. Broad Market ────────────────────────────────────────────────────────
    index_lines   = "\n".join(fmt_quote(q) for q in broad["Indices"])
    vix_lines     = "\n".join(fmt_quote(q) for q in broad["Volatility"])
    sector_lines  = "\n".join(fmt_quote(q) for q in sorted(broad["Sectors"], key=lambda x: x["change_pct"], reverse=True))

    embeds.append({
        "title": "🌐 Broad Market",
        "color": 0x5865F2,
        "fields": [
            {"name": "Indices",    "value": index_lines  or "N/A", "inline": True},
            {"name": "VIX",        "value": vix_lines    or "N/A", "inline": True},
            {"name": "Sectors",    "value": sector_lines or "N/A", "inline": False},
        ]
    })

    # ── 3. Top Movers ──────────────────────────────────────────────────────────
    gainer_lines = "\n".join(fmt_quote(q) for q in gainers)
    loser_lines  = "\n".join(fmt_quote(q) for q in losers)

    embeds.append({
        "title": "🚀 Top Movers (S&P 500 Sample)",
        "color": 0x57F287,
        "fields": [
            {"name": "🔝 Top Gainers", "value": gainer_lines or "N/A", "inline": True},
            {"name": "📉 Top Losers",  "value": loser_lines  or "N/A", "inline": True},
        ]
    })

    # ── 4. Watchlist ───────────────────────────────────────────────────────────
    if watchlist_data:
        wl_lines = "\n".join(fmt_quote(q) for q in watchlist_data)
        embeds.append({
            "title": "👀 Watchlist",
            "color": 0xFEE75C,
            "description": wl_lines
        })

    # ── 5. Volume Spikes ───────────────────────────────────────────────────────
    if spikes:
        spike_lines = "\n".join(fmt_spike(q) for q in spikes)
        embeds.append({
            "title": "⚡ Volume Spikes",
            "description": (
                f"Tickers printing **{VOLUME_SPIKE_THRESHOLD}x+** their 3-month average volume:\n\n"
                + spike_lines
            ),
            "color": 0xEB459E,
            "footer": {"text": "High volume = smart money moving. Direction matters."}
        })

    return embeds

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("Fetching broad market data...")
    broad = {}
    for group, tickers in BROAD_MARKET.items():
        broad[group] = fetch_group(tickers)

    print("Fetching top movers...")
    gainers, losers = get_top_movers(5)

    print("Fetching watchlist...")
    watchlist_tickers = load_watchlist()
    watchlist_data    = fetch_group(watchlist_tickers) if watchlist_tickers else []

    print("Detecting volume spikes...")
    # Check spikes across watchlist + top movers combined
    all_tracked = watchlist_data + gainers + losers
    seen = set()
    unique_tracked = []
    for q in all_tracked:
        if q["ticker"] not in seen:
            seen.add(q["ticker"])
            unique_tracked.append(q)
    spikes = detect_volume_spikes(unique_tracked)

    # Build data dict for Claude
    market_data = {
        "date":        str(date.today()),
        "indices":     broad["Indices"],
        "vix":         broad["Volatility"],
        "sectors":     broad["Sectors"],
        "top_gainers": gainers,
        "top_losers":  losers,
        "watchlist":   watchlist_data,
        "volume_spikes": [
            {
                "ticker":      q["ticker"],
                "spike_ratio": q["spike_ratio"],
                "change_pct":  q["change_pct"],
                "price":       q["price"],
            }
            for q in spikes
        ],
    }

    print("Generating AI summary...")
    summary = get_ai_summary(market_data)

    print("Building Discord embeds...")
    embeds = build_embeds(broad, gainers, losers, watchlist_data, spikes, summary)

    print("Posting to Discord...")
    payload = {"embeds": embeds}
    r = requests.post(DISCORD_WEBHOOK_URL, json=payload)
    if r.status_code in (200, 204):
        print("✅ Digest posted successfully.")
    else:
        print(f"❌ Discord error {r.status_code}: {r.text}")

if __name__ == "__main__":
    main()
