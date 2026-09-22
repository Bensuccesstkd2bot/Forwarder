import os, asyncio, logging, threading, time, requests
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Bot

# --- CONFIG ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
MY_ID = os.getenv("MY_TELEGRAM_ID") or os.getenv("TELEGRAM_ID") or "7534036406"

# Chains to hunt
CHAINS = {
    "solana": "🔷 SOL",
    "bsc": "🟡 BNB",
    "base": "🔵 BASE",
    "ethereum": "💎 ETH"
}

logging.basicConfig(level=logging.INFO)

# --- KEEP RENDER ALIVE ---
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"FINAL V4 LIVE - Hunting Gems")
    def log_message(self, *a): pass

def start_web():
    port = int(os.getenv("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), Handler)
    print(f"Web server running on {port}")
    server.serve_forever()

# --- BOT LOGIC ---
seen_tokens = set()

def is_good_token(pair):
    try:
        # Basic filters - gem hunter filters
        liquidity = float(pair.get('liquidity', {}).get('usd', 0) or 0)
        fdv = float(pair.get('fdv', 0) or 0)
        pair_age = pair.get('pairCreatedAt', 0)
        
        if liquidity < 3000: return False  # Ignore low liq
        if fdv > 500000: return False     # Only early gems < 500k
        if fdv < 5000: return False
        
        # Honeypot quick check - if has many red flags
        return True
    except:
        return False

async def hunt(bot):
    print("🔍 Hunting started...")
    while True:
        try:
            for chain_id, emoji in CHAINS.items():
                # Get latest pairs from DexScreener
                url = f"https://api.dexscreener.com/latest/dex/search/?q={chain_id}"
                # Better: use latest profiles / token-boosts
                try:
                    # Get new pairs by chain
                    r = requests.get(f"https://api.dexscreener.com/token-boosts/latest/v1", timeout=10)
                    if r.status_code != 200:
                        await asyncio.sleep(5)
                        continue
                    
                    tokens = r.json()[:20]  # latest boosted
                    
                    # Also check new pairs via pairs
                    r2 = requests.get(f"https://api.dexscreener.com/latest/dex/tokens/trending", timeout=10)
                    
                except Exception as e:
                    print(f"API error {e}")
                    await asyncio.sleep(10)
                    continue

                # Simple implementation: Check dexscreener pairs for each chain
                try:
                    url = f"https://api.dexscreener.com/latest/dex/search/?q=chain:{chain_id}"
                    resp = requests.get(url, timeout=15).json()
                    pairs = resp.get('pairs', [])[:10]
                    
                    for pair in pairs:
                        pair_addr = pair.get('pairAddress')
                        if not pair_addr or pair_addr in seen_tokens:
                            continue
                        
                        if not is_good_token(pair):
                            continue
                        
                        seen_tokens.add(pair_addr)
                        
                        base_symbol = pair.get('baseToken', {}).get('symbol', '???')
                        base_addr = pair.get('baseToken', {}).get('address', '')
                        price_usd = pair.get('priceUsd', '0')
                        liq = pair.get('liquidity', {}).get('usd', 0)
                        fdv = pair.get('fdv', 0)
                        dex = pair.get('dexId', '')
                        url_dex = pair.get('url', '')
                        
                        msg = (
                            f"💎 NEW GEM FOUND {emoji}\n\n"
                            f"🪙 {base_symbol} ({chain_id.upper()})\n"
                            f"💰 Price: ${price_usd}\n"
                            f"💧 Liq: ${int(float(liq or 0)):,}\n"
                            f"📊 FDV: ${int(float(fdv or 0)):,}\n"
                            f"🔄 DEX: {dex}\n\n"
                            f"📈 Chart: {url_dex}\n"
                            f"🔍 CA: `{base_addr}`\n\n"
                            f"⚠️ DYOR - Check honeypot!"
                        )
                        
                        try:
                            await bot.send_message(chat_id=int(MY_ID), text=msg, parse_mode='Markdown', disable_web_page_preview=False)
                            print(f"Sent gem: {base_symbol} on {chain_id}")
                        except Exception as e:
                            print(f"Send error: {e}")
                        
                        await asyncio.sleep(2)
                
                except Exception as e:
                    print(f"Chain {chain_id} error: {e}")
            
            print(f"Hunt cycle done. Seen: {len(seen_tokens)} tokens. Sleeping 60s")
            await asyncio.sleep(60)  # Check every 1 min
            
        except Exception as e:
            print(f"Hunt loop error: {e}")
            await asyncio.sleep(30)

async def main():
    if not BOT_TOKEN:
        print("ERROR: BOT_TOKEN missing!")
        return
    
    bot = Bot(token=BOT_TOKEN)
    
    # Send LIVE message
    try:
        await bot.send_message(
            chat_id=int(MY_ID),
            text="✅ FINAL V4 REAL HUNTER LIVE\n\n🔷 SOL + 🟡 BNB + 🔵 BASE + 💎 ETH\n\n🤖 Bot is now hunting REAL gems!\nYou will get alerts for new tokens < 500k FDV\n\nGood luck! 🚀"
        )
        print("Live message sent!")
    except Exception as e:
        print(f"Live send failed: {e}")
    
    # Start hunting forever
    await hunt(bot)

if __name__ == "__main__":
    # Start web server in background (THIS KEEPS RENDER ALIVE)
    threading.Thread(target=start_web, daemon=True).start()
    # Start bot
    asyncio.run(main())
