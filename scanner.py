import os, time, logging, requests
from datetime import datetime, timezone

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
S = requests.Session()
S.headers.update({'User-Agent':'PersonalMemeScanner/1.0'})
CHAINS = {x.strip().lower() for x in os.getenv('CHAINS','solana,ethereum,base').split(',')}
MIN_LIQ = float(os.getenv('MIN_LIQUIDITY_USD','25000'))
MIN_VOL = float(os.getenv('MIN_VOLUME_5M_USD','10000'))
MIN_BUYS = int(os.getenv('MIN_BUYS_5M','20'))
MIN_RATIO = float(os.getenv('MIN_BUY_SELL_RATIO','1.5'))
MIN_CHANGE = float(os.getenv('MIN_PRICE_CHANGE_5M','3'))
MAX_AGE = float(os.getenv('MAX_POOL_AGE_HOURS','24'))
POLL = max(60, int(os.getenv('POLL_SECONDS','90')))
KEY = os.environ['PUSHOVER_APP_TOKEN']
USER = os.environ['PUSHOVER_USER_KEY']
last_alert = {}

def get(url):
    r=S.get(url,timeout=15); r.raise_for_status(); return r.json()

def notify(message):
    r = S.post(
        'https://api.pushover.net/1/messages.json',
        data={
            'token': KEY,
            'user': USER,
            'title': 'Meme coin watchlist alert',
            'message': message,
            'priority': 0
        },
        timeout=15
    )
    if not r.ok:
        logging.error('Pushover error: %s', r.text)
    r.raise_for_status()
def candidates():
    # Public discovery endpoint: recent token profiles, not an exhaustive feed of new pools.
    rows=get('https://api.dexscreener.com/token-profiles/latest/v1')
    seen=set()
    for row in rows if isinstance(rows,list) else []:
        chain=str(row.get('chainId','')).lower(); token=row.get('tokenAddress')
        if chain in CHAINS and token and (chain,token) not in seen:
            seen.add((chain,token)); yield chain,token

def evaluate(p):
    liq=float((p.get('liquidity') or {}).get('usd') or 0)
    vol=float((p.get('volume') or {}).get('m5') or 0)
    tx=(p.get('txns') or {}).get('m5') or {}
    buys=int(tx.get('buys') or 0); sells=int(tx.get('sells') or 0)
    change=float((p.get('priceChange') or {}).get('m5') or 0)
    created=p.get('pairCreatedAt')
    if not created: return None
    age=(time.time()*1000-float(created))/3600000
    if not (0 <= age <= MAX_AGE and liq>=MIN_LIQ and vol>=MIN_VOL and buys>=MIN_BUYS and buys/max(sells,1)>=MIN_RATIO and change>=MIN_CHANGE): return None
    return f"{p.get('chainId')} | {p.get('baseToken',{}).get('symbol','?')}\nLiquidity ${liq:,.0f} | 5m volume ${vol:,.0f}\n5m buys/sells {buys}/{sells} | change +{change:.1f}%\nPool age {age:.1f}h\n{p.get('url','')}\nWATCHLIST ONLY — verify contract and exit liquidity before trading."

def scan():
    now=time.time()
    for chain,token in candidates():
        try:
            pairs=get(f'https://api.dexscreener.com/token-pairs/v1/{chain}/{token}')
            for p in pairs if isinstance(pairs,list) else []:
                msg=evaluate(p)
                if not msg: continue
                pairid=f"{chain}:{p.get('pairAddress','')}"
                if now-last_alert.get(pairid,0)<3600: continue
                notify(msg); last_alert[pairid]=now
                logging.info('Alert sent for %s',pairid)
        except Exception as e:
            logging.warning('Skipped %s:%s: %s',chain,token,e)
    for k,v in list(last_alert.items()):
        if now-v>86400: del last_alert[k]

if __name__=='__main__':
    logging.info('Scanner started; discovery is sampled, not exhaustive; alerts are not buy signals')
    while True:
        try: scan()
        except Exception as e: logging.exception('Scan failed: %s',e)
        time.sleep(POLL)
