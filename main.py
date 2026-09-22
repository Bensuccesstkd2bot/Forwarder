import os
import asyncio
import logging
from telegram import Bot
from telegram.error import TelegramError

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
MY_TELEGRAM_ID = os.getenv("MY_TELEGRAM_ID") or os.getenv("TELEGRAM_ID") or "7534036406"

async def main():
    if not BOT_TOKEN:
        print("BOT_TOKEN missing!")
        return
    
    bot = Bot(token=BOT_TOKEN)
    
    # Test message
    try:
        chat_id = int(MY_TELEGRAM_ID)
        await bot.send_message(
            chat_id=chat_id,
            text="✅ FINAL V4 LIVE\n\n🔷 SOL + 🟡 BNB + 🔷 BASE + 🔷 ETH\n\nBot is hunting gems now...\nFilters: LP > $5k | Holders > 20 | No Honeypot\n\nWaiting for new tokens..."
        )
        print(f"Sent LIVE message to {chat_id}")
    except Exception as e:
        print(f"Error sending: {e}")
    
    # Keep alive for Render
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())
