import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Logging setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Apna Telegram Bot Token yahan single quotes me dalein
TOKEN ='8992369160:AAHAoI5PrGlQjGq0F3L78n5ERxvDqdJ9vZ8'


# Command handler for /like
async def like_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.message.reply_text("Kripya UID dalein. Example: `/like 12345678`", parse_mode="Markdown")
        return
    
    uid = args[0]
    keyboard = [
        [InlineKeyboardButton("👍 Like Bhejo", callback_data=f"send_like_{uid}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"🎮 **Free Fire Player Info**\n🆔 UID: `{uid}`\n\nNeeche diye gaye button par click karke like bhejiye:",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

def main():
    application = ApplicationBuilder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("like", like_command))
    
    print("Starting Manjeet Free Fire Like Bot...")
    application.run_polling()

if __name__ == '__main__':
    main()
