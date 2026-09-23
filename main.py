import os, asyncio, threading, time, requests
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Bot

BOT_TOKEN = os.getenv("BOT_TOKEN")
MY_ID = os.getenv("MY_TELEGRAM_ID") or os.getenv("TELEGRAM_ID") or "7534036406"
seen = set()

class H(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200); self.end_headers(); self.wfile.write(b"V4.2 LIVE - TEST MODE")
    def log_message(self,*a): pass

def start_web():
    port=int(os.getenv("PORT",10000))
    HTTPServer(("0.0.0.0",port),H).serve_forever()

def check_security(chain, ca):
    try:
        if chain == "solana":
            return True, 0, 0, "SOL - DYOR"
        # Map chain name to GoPlus ID
        chain_map = {"ethereum":"1","bsc":"56","base":"8453"}
        gid = chain_map.get(chain, "1")
        url = f"https://api.gopluslabs.io/api/v1/token_security/{gid}?contract_addresses={ca}"
        r = requests.get(url, timeout=10).json()
        data = r.get('result', {}).get(ca.lower(), {})
        if not data:
            return True, 0, 0, "No Data"
        buy_tax = float(data.get('buy_tax',0) or 0)
        sell_tax = float(data.get('sell_tax',0) or 0)
        if data.get('is_honeypot') == '1':
            return False, buy_tax, sell_tax, "HONEYPOT"
        if buy_tax > 15 or sell_tax > 15:
            return False, buy_tax, sell_tax, f"High Tax {buy_tax}/{sell_tax}%"
        return True, buy_tax, sell_tax, f"Safe"
    except:
        return True, 0, 0, "Check Skip"

def is_gem(pair):
    try:
        liq = float(pair.get('liquidity',{}).get('usd',0) or 0)
        fdv = float(pair.get('fdv',0) or 0)
        vol = float(pair.get('volume',{}).get('h24',0) or 0)
        # V4.2 LOOSER - TO GET GEMS!
        if liq < 3000: return False
        if fdv < 5000 or fdv > 600000: return False
        if vol < 300: return False
        # Age < 48h
        created = pair.get('pairCreatedAt',0)
        if created:
            age_h = (time.time()*1000 - created)/(1000*3600)
            if age_h > 48: return False
        return True
    except:
        return False

async def hunt(bot):
    print("V4.2 Hunting started - LOOSER FILTERS")
    while True:
        try:
            # NEW: Use real fresh feed - boosts + profiles
            urls = [
                "https://api.dexscreener.com/token-boosts/latest/v1",
                "https://api.dexscreener.com/token-profiles/latest/v1"
            ]
            all_tokens = []
            for u in urls:
                try:
                    r = requests.get(u, timeout=12).json()
                    if isinstance(r, list):
                        all_tokens.extend(r[:20])
                except: pass

            print(f"Checking {len(all_tokens)} fresh tokens...")

            for item in all_tokens:
                try:
                    ca = item.get('tokenAddress')
                    chain = item.get('chainId')
                    if not ca or not chain: continue
                    if ca in seen: continue

                    # Get pair data for this CA
                    resp = requests.get(f"https://api.dexscreener.com/latest/dex/tokens/{ca}", timeout=12).json()
                    pairs = resp.get('pairs', [])
                    if not pairs: continue
                    pair = pairs[0] # take main pair

                    p_addr = pair.get('pairAddress')
                    if p_addr in seen: continue
                    if not is_gem(pair):
                        print(f"Skip {pair.get('baseToken',{}).get('symbol')} - not gem liq/fdv")
                        continue

                    # Security
                    is_safe, bt, st, safety = check_security(chain, ca)
                    if not is_safe:
                        print(f"Blocked {ca[:6]} {safety}")
                        seen.add(ca); seen.add(p_addr)
                        continue

                    seen.add(ca); seen.add(p_addr)
                    symbol = pair.get('baseToken',{}).get('symbol','?')
                    price = pair.get('priceUsd','0')
                    liq = pair.get('liquidity',{}).get('usd',0)
                    fdv = pair.get('fdv',0)
                    chart = pair.get('url','')

                    emoji = {"solana":"🔷 SOL","bsc":"🟡 BNB","base":"🔵 BASE","ethereum":"💎 ETH"}.get(chain, chain.upper())

                    msg = (
                        f"💎 V4.2 GEM {emoji}\n\n"
                        f"🪙 ${symbol}\n"
                        f"💰 ${price}\n"
                        f"💧 Liq: ${int(float(liq or 0)):,}\n"
                        f"📊 FDV: ${int(float(fdv or 0)):,}\n"
                        f"🛡️ {safety} | Tax {bt}/{st}%\n"
                        f"📈 {chart}\n"
                        f"`{ca}`"
                    )
                    await bot.send_message(chat_id=int(MY_ID), text=msg, parse_mode='Markdown', disable_web_page_preview=True)
                    print(f"SENT {symbol}")
                    await asyncio.sleep(2)
                except Exception as e:
                    print(f"Token error {e}")

            await asyncio.sleep(35)
        except Exception as e:
            print(f"Loop error {e}")
            await asyncio.sleep(20)

async def main():
    bot = Bot(BOT_TOKEN)
    # === V4.2 TEST GEM - YOU WILL SEE THIS! ===
    try:
        await bot.send_message(chat_id=int(MY_ID), text="✅ V4.2 TEST - BOT IS LIVE AND WORKING!\n\nIf you see this, connection is OK. Now hunting real gems...\n\nFilters: Liq >3k, FDV 5k-600k, Age <48h", parse_mode='Markdown')
        print("TEST GEM SENT!")
    except Exception as e:
        print(f"Test fail {e}")

    await hunt(bot)

if __name__ == "__main__":
    threading.Thread(target=start_web, daemon=True).start()
    asyncio.run(main())
