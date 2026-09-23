# V4.2 - ULTIMATE DEBUG + TEST GEM MODE
# This version sends test signal on startup + logs every block reason

import asyncio
# ... (your existing imports)

# === NEW: TEST ON STARTUP ===
async def send_test_gem():
    await asyncio.sleep(10) # wait for bot to connect
    test_message = """
🚀✅ V4.2 TEST GEM - BOT IS LIVE!

If you see this, your bot WORKS!

CA: 0x123...TEST (Not real token)
Chain: BSC
FDV: $150k
Liq: $12k
Tax: 3%/3%
Honeypot: SAFE ✅

This is only a test. Real gems will come next.
    """
    await client.send_message(DEST_CHANNEL_ID, test_message)
    print("✅ TEST GEM SENT!")

# Call it on startup
client.loop.create_task(send_test_gem())
