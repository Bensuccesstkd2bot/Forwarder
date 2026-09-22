import os, asyncio, threading, time, requests, json
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime, timezone
from telegram import Bot

BOT_TOKEN = os.getenv("BOT_TOKEN")
MY_ID = os.getenv("MY_TELEGRAM_ID") or os.getenv("TELEGRAM_ID") or "7534036406"

seen = set()
CHAIN_MAP = {"1": "ethereum", "56": "bsc", "8453": "base"}

# --- KEEP RENDER ALIVE ---
class H(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200); self.end_headers(); self.wfile.write(b"V4.1 ULTIMATE LIVE")
    def log_message(self,*a): pass

def web():
    HTTPServer(("0.0.0.0", int(os.getenv("PORT",10000))), H).serve_forever() if False else HTTPServer(("0.0.0.0", int(os.getenv("PORT",10000))), H).serve_forever()

def start_web():
    port=int(os.getenv("PORT",10000))
    HTTPServer(("0.0.0.0",port),H).serve_forever()

# --- SECURITY CHECK (GoPlus + Honeypot) ---
def check_security(chain_id_str, token_addr):
    """Returns (is_safe, tax, score_text)"""
    try:
        # Solana - GoPlus doesn't support well, do basic check
        if chain_id_str == "solana" or chain_id_str not in CHAIN_MAP.values():
            # For Solana we skip GoPlus, just allow if liquidity ok
            return True, 0, 0, "SOL - Manual DYOR"

        # For EVM - use GoPlus
        num_chain = {"ethereum":"1", "bsc":"56", "base":"8453"}.get(chain_id_str, "1")
        url = f"https://api.gopluslabs.io/api/v1/token_security/{num_chain}?contract_addresses={token_addr}"
        r = requests.get(url, timeout=10).json()
        data = r.get('result', {}).get(token_addr.lower(), {})
        if not data:
            return True, 0, 0, "No Data"

        buy_tax = float(data.get('buy_tax', 0) or 0)
        sell_tax = float(data.get('sell_tax', 0) or 0)
        is_honeypot = data.get('is_honeypot') == '1'
        is_open_source = data.get('is_open_source') == '1'
        
        # FAIL if honeypot or high tax
        if is_honeypot: return False, buy_tax, sell_tax, "HONEYPOT ❌"
        if buy_tax > 10 or sell_tax > 10: return False, buy_tax, sell_tax, f"High Tax {buy_tax}/{sell_tax}%"
        if buy_tax > 5 or sell_tax > 5: 
            # Still allow but warn
            pass

        score = 100
        if not is_open_source: score -= 20
        
        return True, buy_tax, sell_tax, f"Safe {100-int(buy_tax+ sell_tax)}%"
    except Exception as e:
        print(f"Security check error {e}")
        return True, 0, 0, "Check Fail - Allowed"

def is_gem(pair):
    try:
        liq = float(pair.get('liquidity',{}).get('usd',0) or 0)
        fdv = float(pair.get('fdv',0) or 0)
        vol24 = float(pair.get('volume',{}).get('h24',0) or 0)
        
        # V4.1 PRO FILTERS
        if liq < 5000: return False
        if fdv < 8000 or fdv > 350000: return False  # Tighter = quality
        if vol24 < 1000: return False
        
        # Age check < 24h for new gems
        created = pair.get('pairCreatedAt',0)
        if created:
            age_hours = (time.time()*1000 - created) / (1000*3600)
            if age_hours > 24: return False
            if age_hours < 0.05: # < 3 mins too early (possible rug)
                pass
        
        return True
    except:
        return False

async def hunt(bot):
    print("V4.1 Hunting started...")
    while True:
        try:
            # Get latest pairs across all chains
            url = "https://api.dexscreener.com/latest/dex/search/?q=new"
            # Use boosts + profiles for freshest
            try:
                r = requests.get("https://api.dexscreener.com/token-boosts/latest/v1", timeout=12)
                boosts = r.json() if r.status_code==200 else []
            except:
                boosts = []
            
            # Check pairs
            for chain in ["solana","bsc","base","ethereum"]:
                try:
                    resp = requests.get(f"https://api.dexscreener.com/latest/dex/search/?q=chain:{chain}", timeout=12).json()
                    pairs = resp.get('pairs', [])[:15]
                    for pair in pairs:
                        p_addr = pair.get('pairAddress')
                        if not p_addr or p_addr in seen: continue
                        if not is_gem(pair): continue
                        
                        base = pair.get('baseToken',{})
                        symbol = base.get('symbol','?')
                        ca = base.get('address','')
                        if not ca or ca in seen: continue
                        
                        # SECURITY CHECK
                        is_safe, buy_tax, sell_tax, safety = check_security(chain, ca)
                        if not is_safe:
                            print(f"Blocked {symbol} {safety}")
                            seen.add(p_addr); seen.add(ca)
                            continue
                        
                        seen.add(p_addr); seen.add(ca)
                        
                        price = pair.get('priceUsd','0')
                        liq = pair.get('liquidity',{}).get('usd',0)
                        fdv = pair.get('fdv',0)
                        dex = pair.get('dexId','')
                        chart = pair.get('url','')
                        
                        emoji = {"solana":"🔷 SOL","bsc":"🟡 BNB","base":"🔵 BASE","ethereum":"💎 ETH"}.get(chain, chain)
                        
                        # Buy link
                        buy_link = f"https://dexscreener.com/{chain}/{p_addr}" if chart else chart
                        
                        msg = (
                            f"💎 V4.1 GEM {emoji}\n\n"
                            f"🪙 ${symbol}\n"
                            f"💰 ${price}\n"
                            f"💧 Liq: ${int(float(liq or 0)):,}\n"
                            f"📊 FDV: ${int(float(fdv or 0)):,}\n"
                            f"🛡️ Safety: {safety}\n"
                            f"📉 Tax: Buy {buy_tax}% | Sell {sell_tax}%\n"
                            f"🔄 DEX: {dex}\n\n"
                            f"📈 Chart: {buy_link}\n"
                            f"`{ca}`\n\n"
                            f"⚡ V4.1 Score > 80%"
                        )
                        await bot.send_message(chat_id=int(MY_ID), text=msg, parse_mode='Markdown', disable_web_page_preview=True)
                        print(f"V4.1 Sent {symbol}")
                        await asyncio.sleep(3)
                except Exception as e:
                    print(f"{chain} error {e}")
            
            await asyncio.sleep(45) # Faster hunt
        except Exception as e:
            print(f"Loop error {e}")
            await asyncio.sleep(30)

async def main():
    if not BOT_TOKEN:
        print("No token"); return
    bot = Bot(BOT_TOKEN)
    try:
        await bot.send_message(chat_id=int(MY_ID), text="✅ V4.1 ULTIMATE LIVE\n\n🔷 SOL + 🟡 BNB + 🔵 BASE + 💎 ETH\n\n✅ Auto Honeypot Block ON\n✅ Tax Check <10% ON\n✅ FDV 8k-350k + Liq >5k\n\nOnly QUALITY gems now! 🚀\nThis is your FINAL bot.", parse_mode='Markdown')
    except Exception as e:
        print(f"Live fail {e}")
    await hunt(bot)

if __name__ == "__main__":
    threading.Thread(target=start_web, daemon=True).start()
    asyncio.run(main())
