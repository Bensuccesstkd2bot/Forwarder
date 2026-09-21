import os
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

BOT_TOKEN = os.environ.get("BOT_TOKEN")
FORWARD_MAP = { -1004427378689: -1004427378589 }

async def forward(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.channel_post or update.message
    if not msg: return
    dest = FORWARD_MAP.get(update.effective_chat.id)
    if not dest: return
    try:
        await context.bot.copy_message(chat_id=dest, from_chat_id=update.effective_chat.id, message_id=msg.message_id)
    except Exception as e:
        print(e)

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.ALL, forward))
    app.run_polling(allowed_updates=["message","channel_post"], drop_pending_updates=True)

if __name__ == "__main__":
    main()
