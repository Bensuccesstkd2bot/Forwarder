
import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

BOT_TOKEN = os.environ.get("BOT_TOKEN")
FORWARD_MAP = { -1004427378609: -1004427378589 }

async def forward(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.channel_post or update.message
    if not msg:
        return
    dest = FORWARD_MAP.get(update.effective_chat.id)
    if not dest:
        return
    try:
        await context.bot.copy_message(chat_id=dest, from_chat_id=update.effective_chat.id, message_id=msg.message_id)
    except Exception as e:
        print(e)

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.ALL, forward))
    app.run_polling(allowed_updates=["message", "channel_post"], drop_pending_updates=True)

class FakeHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running")

def run_fake_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), FakeHandler)
    server.serve_forever()

if __name__ == "__main__":
    threading.Thread(target=run_fake_server, daemon=True).start()
    main()
