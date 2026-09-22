
import os
import asyncio
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
from telegram import Bot

logging.basicConfig(level=logging.INFO)
BOT_TOKEN = os.getenv("BOT_TOKEN")
MY_ID = os.getenv("MY_TELEGRAM_ID") or os.getenv("TELEGRAM_ID") or "7534036406"

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is LIVE")
    def log_message(self, *args):
        pass

def start_web():
    port = int(os.getenv("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), Handler)
    print(f"Web server on {port}")
    server.serve_forever()

async def send_live():
    if not BOT_TOKEN:
        print("No BOT_TOKEN")
        return
    bot = Bot(token=BOT_TOKEN)
    try:
        await bot.send_message(chat_id=int(MY_ID), text="✅ FINAL V4 LIVE\n\n🔷 SOL + 🟡 BNB + 🔷 BASE + 🔷 ETH\nBot is hunting gems now...\nWaiting for new tokens...")
        print("LIVE sent!")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    threading.Thread(target=start_web, daemon=True).start()
    asyncio.run(send_live())
    while True:
        asyncio.run(asyncio.sleep(3600))
