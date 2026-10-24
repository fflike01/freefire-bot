import os
import logging
import threading

import httpx
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

# Logging setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# ---------------- SETTINGS ----------------
# Token yahan code mein MAT likho (repo public hai).
# Render > Environment mein BOT_TOKEN naam se daalo.
TOKEN = os.environ.get("BOT_TOKEN", "8992369160:AAHmh4k6yNkjR_YtKH45p7Ni4P1mG5UAO9s")

# Like API ka URL. Render > Environment mein LIKE_API_URL naam se daalo.
# {uid} jahan UID aana hai wahan likho. Example:
# https://example.com/like?uid={uid}
LIKE_API_URL = os.environ.get("LIKE_API_URL", "")
# ------------------------------------------

# Chhota web server (Render free Web Service ke liye port chahiye)
web = Flask(__name__)


@web.route("/")
def home():
    return "Bot running"


def run_web():
    web.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))


# Command handler for /start
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Namaste! Free Fire like bot mein swagat hai.\n"
        "Use karein: `/like UID`\nExample: `/like 12345678`",
        parse_mode="Markdown"
    )


# Command handler for /like
async def like_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.message.reply_text(
            "Kripya UID dalein. Example: `/like 12345678`",
            parse_mode="Markdown"
        )
        return

    uid = args[0]
    if not uid.isdigit():
        await update.message.reply_text("UID sirf numbers mein hona chahiye.")
        return

    keyboard = [
        [InlineKeyboardButton("👍 Like Bhejo", callback_data=f"send_like_{uid}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"🎮 **Free Fire Player Info**\n🆔 UID: `{uid}`\n\nNeeche diye gaye button par click karke like bhejiye:",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )


# Button click handler
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data or ""
    if not data.startswith("send_like_"):
        return

    uid = data.replace("send_like_", "", 1)

    if not LIKE_API_URL:
        await query.edit_message_text(
            f"⚠️ Like API set nahi hai.\nUID: `{uid}`\n"
            "Render Environment mein LIKE_API_URL daalein.",
            parse_mode="Markdown"
        )
        return

    await query.edit_message_text(f"⏳ UID `{uid}` par like bheja ja raha hai...", parse_mode="Markdown")

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(LIKE_API_URL.format(uid=uid))
        if resp.status_code == 200:
            text = f"✅ Request bhej di gayi.\nUID: `{uid}`\n\nJawab:\n`{resp.text[:300]}`"
        else:
            text = f"❌ API error {resp.status_code}\nUID: `{uid}`"
    except Exception as e:
        logging.error("Like API error: %s", e)
        text = f"❌ API se connect nahi ho paya.\nUID: `{uid}`"

    await query.edit_message_text(text, parse_mode="Markdown")


def main():
    if not TOKEN:
        raise SystemExit("BOT_TOKEN set nahi hai. Render > Environment mein daalein.")

    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("like", like_command))
    application.add_handler(CallbackQueryHandler(button_handler))

    threading.Thread(target=run_web, daemon=True).start()

    print("Starting Manjeet Free Fire Like Bot...")
    application.run_polling()


if __name__ == '__main__':
    main()
