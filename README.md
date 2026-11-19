# Meme Coin Watchlist Scanner

Python polling worker using public DexScreener token-profile discovery and token-pair data, sending Pushover alerts. **Not exhaustive, not tick-by-tick, and not a trading signal.** No wallet integration.

## Local run

Install Python 3.11+ and run `pip install -r requirements.txt`. Set `PUSHOVER_APP_TOKEN` and `PUSHOVER_USER_KEY` in your environment; run `python scanner.py`.

## Railway deployment

1. Upload this folder to a private GitHub repository (do not include secrets).
2. In Railway, create a new project from that GitHub repo. Use a worker service (no public domain needed).
3. Set variables `PUSHOVER_APP_TOKEN`, `PUSHOVER_USER_KEY`, and optionally `CHAINS=solana,ethereum,base`, `MIN_LIQUIDITY_USD=25000`, `MIN_VOLUME_5M_USD=10000`, `MIN_BUYS_5M=20`, `MIN_BUY_SELL_RATIO=1.5`, `MIN_PRICE_CHANGE_5M=3`, `MAX_POOL_AGE_HOURS=24`, `POLL_SECONDS=90`.
4. Deploy and review logs. Send a test notification separately via Pushover's API or test it in the Pushover dashboard before relying on alerts.

## Caveats

- DexScreener's latest token profiles endpoint is a discovery sample, not all new tokens, and may overrepresent promoted tokens. The scanner checks available pairs for discovered tokens only.
- Public API limits and availability may change. The 90-second cycle is a target; network calls and limits can slow it.
- No contract-security, honeypot, rug-pull, or holder-concentration checks are implemented. **Never assume a token is safe because an alert fires.**
- Alerts may be delayed or missed due to provider limits, outages, or push notification delivery.
- Deploying a continuously running Railway service may incur hosting charges.
