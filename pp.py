import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Logging setup karein
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Token kura biya yehi
TOKEN = '8840230555:AAE588ET-noyUBnw-TaRwf-twUMxiuzQFtI'
LIKE_API_URL = os.getenv("LIKE_API_URL", "https://jsonplaceholder.typicode.com/posts")

# /start command handler
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Namaste! Free Fire Like Bot me aapka swagat hai.\n\n"
        "Like bhejne ke liye yeh command use karein:\n"
        "/like <Aapka_UID>"
    )

# /like command handler
async def like_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.message.reply_text("Kripya UID dalein. Example: `/like 12345678`", parse_mode="Markdown")
        return

    uid = args[0]
    
    # Inline button banana
    keyboard = [
        [InlineKeyboardButton("👍 Like Bhejo", callback_data=f"send_like_{uid}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"Target UID: `{uid}`\nNeeche diye gaye button par click karke process shuru karein:",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

def main():
    # Application build karein
    application = ApplicationBuilder().token(TOKEN).build()

    # Handlers add karein
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("like", like_command))

    logger.info("Bot successfully start ho raha hai...")
    
    # Bot ko run karne ke liye polling shuru karein
    application.run_polling()

if __name__ == '__main__':
    main()
    
