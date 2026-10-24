
import os
import re
import time
import logging
import asyncio

import httpx
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import TelegramError
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

# ============== SETTINGS ==============
BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
API_URL = os.getenv("LIKE_API_URL", "").strip()
API_KEY = os.getenv("LIKE_API_KEY", "").strip()

# Change these settings to match your API documentation.
API_METHOD = os.getenv("API_METHOD", "GET").strip().upper()
UID_PARAM = os.getenv("UID_PARAM", "uid").strip()
API_KEY_HEADER = os.getenv("API_KEY_HEADER", "Authorization").strip()
API_KEY_PREFIX = os.getenv("API_KEY_PREFIX", "Bearer ").strip()

COOLDOWN = 10
REQUEST_TIMEOUT = 20

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
log = logging.getLogger("LikeBot")

user_last_request = {}
user_locks = {}


def valid_uid(uid):
    return bool(re.fullmatch(r"[0-9]{5,20}", uid))


def main_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("👍 Request Likes", callback_data="instructions")],
        [InlineKeyboardButton("ℹ️ Help", callback_data="help")],
    ])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        "🎮 FREE FIRE LIKE BOT\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        "Welcome! Use the commands below.\n\n"
        "• /like YOUR_UID\n"
        "• /help\n\n"
        "Actual likes require a working API provider.",
        reply_markup=main_keyboard(),
    )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        "📘 HOW TO USE\n\n"
        "1. Send /like followed by your numeric UID.\n"
        "2. Check the UID shown by the bot.\n"
        "3. Press Confirm to submit the request.\n\n"
        "Commands:\n"
        "/start - Main menu\n"
        "/like UID - Submit a request\n"
        "/help - Instructions"
    )


async def like_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.effective_message.reply_text(
            "Please enter your UID.\nExample: /like 12345678"
        )
        return

    uid = context.args[0].strip()

    if not valid_uid(uid):
        await update.effective_message.reply_text(
            "Invalid UID format. Use 5–20 digits only."
        )
        return

    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton(
            "✅ Confirm Request",
            callback_data=f"confirm:{uid}",
        )
    ]])

    await update.effective_message.reply_text(
        f"🎯 UID: {uid}\n\nConfirm your request below.",
        reply_markup=keyboard,
    )


async def call_like_api(uid):
    if not API_URL:
        return None, "API_NOT_CONFIGURED"

    if API_METHOD not in ("GET", "POST"):
        return None, "INVALID_API_METHOD"

    headers = {"Accept": "application/json"}

    if API_KEY:
        headers[API_KEY_HEADER] = API_KEY_PREFIX + API_KEY

    # GET sends UID in query parameters.
    # POST sends UID in a JSON body.
    try:
        async with httpx.AsyncClient(
            timeout=REQUEST_TIMEOUT,
            follow_redirects=False,
        ) as client:
            if API_METHOD == "GET":
                response = await client.get(
                    API_URL,
                    params={UID_PARAM: uid},
                    headers=headers,
                )
            else:
                response = await client.post(
                    API_URL,
                    json={UID_PARAM: uid},
                    headers=headers,
                )

        if not 200 <= response.status_code < 300:
            log.warning("API HTTP status: %s", response.status_code)
            return None, f"API_HTTP_{response.status_code}"

        try:
            data = response.json()
        except ValueError:
            return None, "API_NON_JSON_RESPONSE"

        if not isinstance(data, dict):
            return None, "API_UNEXPECTED_RESPONSE"

        return data, None

    except httpx.TimeoutException:
        return None, "API_TIMEOUT"
    except httpx.RequestError:
        log.exception("API network error")
        return None, "API_NETWORK_ERROR"
    except Exception:
        log.exception("Unexpected API error")
        return None, "API_ERROR"


async def confirm_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query
    await query.answer()

    data = query.data or ""

    if data == "help":
        await query.message.reply_text(
            "Use /like YOUR_UID to start.\n"
            "Example: /like 12345678"
        )
        return

    if data == "instructions":
        await query.message.reply_text(
            "Send /like followed by your numeric UID."
        )
        return

    match = re.fullmatch(r"confirm:([0-9]{5,20})", data)
    if not match:
        await query.edit_message_text("Invalid or expired request.")
        return

    uid = match.group(1)
    user_id = query.from_user.id
    now = time.monotonic()
    previous = user_last_request.get(user_id, 0)

    if now - previous < COOLDOWN:
        wait = max(1, int(COOLDOWN - (now - previous)) + 1)
        await query.answer(
            f"Please wait {wait} seconds.",
            show_alert=True,
        )
        return

    lock = user_locks.setdefault(user_id, asyncio.Lock())

    if lock.locked():
        await query.answer(
            "Your previous request is still processing.",
            show_alert=True,
        )
        return

    async with lock:
        user_last_request[user_id] = time.monotonic()

        await query.edit_message_text(
            f"⏳ Checking API for UID {uid}..."
        )

        result, error = await call_like_api(uid)

        if error:
            messages = {
                "API_NOT_CONFIGURED":
                    "API URL missing. Add LIKE_API_URL in Replit Secrets.",
                "INVALID_API_METHOD":
                    "API_METHOD must be GET or POST.",
                "API_TIMEOUT":
                    "The API took too long to respond. Try again later.",
                "API_NETWORK_ERROR":
                    "Could not reach the API. Check the URL and connection.",
                "API_NON_JSON_RESPONSE":
                    "The API did not return JSON. Check its documentation.",
                "API_UNEXPECTED_RESPONSE":
                    "The API returned an unexpected data format.",
                "API_ERROR":
                    "An internal error occurred while contacting the API.",
            }

            message = messages.get(
                error,
                "The API rejected the request. Check API settings."
            )
            await query.edit_message_text("❌ " + message)
            return

        # Display only fields that actually exist in the provider response.
        lines = ["📋 API RESPONSE", "", f"🎯 UID: {uid}"]

        status = result.get("status")
        message = result.get("message")
        likes = result.get("likes", result.get("added_likes"))
        nickname = result.get("nickname", result.get("name"))

        if status is not None:
            lines.append(f"Status: {str(status)[:150]}")
        if nickname is not None:
            lines.append(f"Player: {str(nickname)[:100]}")
        if likes is not None:
            lines.append(f"Likes reported: {str(likes)[:50]}")
        if message is not None:
            lines.append(f"Message: {str(message)[:250]}")

        if len(lines) == 3:
            lines.append(
                "API responded successfully, but its response fields "
                "need to be mapped using the provider documentation."
            )

        await query.edit_message_text("\n".join(lines))


async def error_handler(
    update: object,
    context: ContextTypes.DEFAULT_TYPE,
):
    log.error(
        "Unhandled Telegram bot error",
        exc_info=context.error,
    )


def main():
    if not BOT_TOKEN:
        raise RuntimeError(
            "BOT_TOKEN is missing. Add it in Replit Secrets."
        )

    if API_URL and not API_URL.startswith("https://"):
        raise RuntimeError("LIKE_API_URL must use HTTPS.")

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("like", like_cmd))
    app.add_handler(
        CallbackQueryHandler(
            confirm_callback,
            pattern=r"^(confirm:[0-9]{5,20}|instructions|help)$",
        )
    )
    app.add_error_handler(error_handler)

    log.info("Bot starting...")
    app.run_polling(drop_pending_updates=False)


if __name__ == "__main__":
    main()
    
