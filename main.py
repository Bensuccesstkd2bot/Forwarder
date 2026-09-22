import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

BOT_TOKEN = os.environ.get("BOT_TOKEN")
FORWARD_MAP = { -10044443414794: -1004427378589 }

async def forward(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.channel_post or update.message
    if not msg:
        return
    chat_id = update.effective_chat.id
    print(f"Received message in {chat_id}: {msg.text or msg.caption}")
    dest = FORWARD_MAP.get(chat_id)
    if not dest:
        print(f"No destination for {chat_id}")
        return
    print(f"Forwarding to {dest}...")
    try:
        await context.bot.copy_message(chat_id=dest, from_chat_id=chat_id, message_id=msg.message_id)
        print("Forwarded OK!")
    except Exception as e:
        print(f"Forward FAILED: {e}")

def main():
    print("Bot starting...")
    print(f"Watching: {list(FORWARD_MAP.keys())}")
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.ALL, forward))
    app.run_polling(allowed_updates=["message", "channel_post"], drop_pending_updates=True)

class FakeHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running")
    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()

def run_fake_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), FakeHandler)
    print(f"Fake server on port {port}")
    server.serve_forever()

if __name__ == "__main__":
    threading.Thread(target=run_fake_server, daemon=True).start()
    main()
