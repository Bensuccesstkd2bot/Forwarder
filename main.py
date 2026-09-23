import os, asyncio, threading, time, requests
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Bot

BOT_TOKEN = os.getenv("BOT_TOKEN")
MY_ID = os.getenv("MY_TELEGRAM_ID") or os.getenv("TELEGRAM_ID") or "7534036406"
seen = set()

ALLOWED_CHAINS = ["solana", "bsc", "base", "ethereum"] # NO MORE ROBINHOOD

class H(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200); self.end_headers(); self.wfile.write(b"V4.3 SNIPER LIVE")
    def log_message(self,*a): pass

def start_web():
    HTTPServer(("0.0.0.0",int(os.getenv("PORT",10000))),H).serve_forever()

def check_security(chain, ca):
    try:
        if chain == "solana": return True, 0, 0, "SOL"
        chain_map = {"ethereum":"1","bsc":"56","base":"8453"}
        gid = chain_map.get(chain, "1")
        url = f"https://api.gopluslabs.io/api/v1/token_security/{gid}?contract_addresses={ca}"
        r = requests.get(url, timeout=10).json()
        data = r.get('result', {}).get(ca.lower(), {})
        if not data: return True, 0, 0, "No Data"
        bt = float(data.get('buy_tax',0) or 0); st = float(data.get('sell_tax',0) or 0)
        if data.get('is_honeypot') == '1': return False, bt, st, "HONEYPOT"
        if bt > 15 or st > 15: return False, bt, st, f"Tax {bt}/{st}%"
        return True, bt, st, "Safe"
    except: return True, 0, 0, "Skip"

def is_gem(pair):
    try:
        liq = float(pair.get('liquidity',{}).get('usd',0) or 0)
        fdv = float(pair.get('fdv',0) or 0)
        if liq < 8000: return False
        if fdv < 10000 or fdv > 600000: return False
        return True
    except: return False

async def hunt(bot):
    while True:
        try:
            r = requests.get("https://api.dexscreener.com/token-boosts/latest/v1", timeout=12).json()
            for item in r[:30]:
                ca = item.get('tokenAddress'); chain = item.get('chainId')
                if not ca or chain not in ALLOWED_CHAINS: continue
                if ca in seen: continue
                try:
                    resp = requests.get(f"https://api.dexscreener.com/latest/dex/tokens/{ca}", timeout=12).json()
                    pairs = resp.get('pairs', [])
                    if not pairs: continue
                    pair = pairs[0]
                    if not is_gem(pair): continue
                    is_safe, bt, st, safety = check_security(chain, ca)
                    if not is_safe: continue
                    seen.add(ca)
                    symbol = pair.get('baseToken',{}).get('symbol','?')
                    liq = pair.get('liquidity',{}).get('usd',0)
                    fdv = pair.get('fdv',0)
                    chart = pair.get('url','')
                    emoji = {"solana":"🔷 SOL","bsc":"🟡 BNB","base":"🔵 BASE","ethereum":"💎 ETH"}.get(chain, chain)
                    msg = f"💎 V4.3 GEM {emoji}\n\n🪙 ${symbol}\n💧 Liq: ${int(float(liq)):,}\n📊 FDV: ${int(float(fdv)):,}\n🛡️ {safety} {bt}/{st}%\n📈 {chart}\n`{ca}`"
                    await bot.send_message(chat_id=int(MY_ID), text=msg, parse_mode='Markdown', disable_web_page_preview=True)
                    await asyncio.sleep(2)
                except: pass
            await asyncio.sleep(40)
        except: await asyncio.sleep(20)

async def main():
    bot = Bot(BOT_TOKEN)
    try: await bot.send_message(chat_id=int(MY_ID), text="✅ V4.3 SNIPER LIVE\n\n🔷 SOL + 🟡 BNB + 🔵 BASE + 💎 ETH only\n❌ Robinhood BLOCKED\n✅ Liq >8k | FDV 10k-600k\n\nQuality only!", parse_mode='Markdown')
    except: pass
    await hunt(bot)

if __name__ == "__main__":
    threading.Thread(target=start_web, daemon=True).start()
    asyncio.run(main())
