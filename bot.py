import time
import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = os.getenv("8416883655:AAHXQBlS383CbgiaTdSV_aTpc0YdaRnM9c0")

user_cooldown = {}
COOLDOWN_TIME = 15


# ===============================
def check_email(email):
    try:
        url = f"https://vi.emailfake.com/{email}"
        res = requests.get(url, timeout=15)

        if res.status_code != 200:
            return "error"

        text = res.text.lower()

        keywords = [
            "access deactivated",
            "deactivating your access",
            "violated our policies",
            "account has been deactivated",
            "not permitted under our policies",
            "openai team"
        ]

        if any(k in text for k in keywords):
            return "locked"

        return "safe"

    except requests.Timeout:
        return "timeout"
    except requests.ConnectionError:
        return "connection_error"
    except Exception:
        return "error"


# ===============================
async def scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    now = time.time()

    # Anti spam
    if user_id in user_cooldown:
        remaining = COOLDOWN_TIME - (now - user_cooldown[user_id])
        if remaining > 0:
            await update.message.reply_text(
                f"⛔ Vui lòng đợi {int(remaining)} giây"
            )
            return

    if not context.args:
        await update.message.reply_text(
            "Dùng:\n/scan email1 email2 email3"
        )
        return

    emails = context.args[:3]
    user_cooldown[user_id] = now

    status = await update.message.reply_text("🔍 Đang scan...")

    locked = []
    safe = []
    errors = []

    total = len(emails)

    for i, email in enumerate(emails, start=1):
        await status.edit_text(
            f"🔍 Đang scan ({i}/{total})\n📧 {email}"
        )

        result = check_email(email)

        if result == "locked":
            locked.append(email)
        elif result == "safe":
            safe.append(email)
        else:
            errors.append(email)

    result_text = "📊 KẾT QUẢ SCAN\n\n"

    if locked:
        result_text += "🚨 MAIL KHÓA:\n"
        for e in locked:
            result_text += f"   • {e}\n"
        result_text += "\n"

    if safe:
        result_text += "✅ MAIL AN TOÀN:\n"
        for e in safe:
            result_text += f"   • {e}\n"
        result_text += "\n"

    if errors:
        result_text += "⚠️ LỖI / TIMEOUT:\n"
        for e in errors:
            result_text += f"   • {e}\n"

    if not locked and not safe:
        result_text += "Không có kết quả"

    await status.edit_text(result_text)


# ===============================
def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("scan", scan))

    print("BOT ĐANG CHẠY...")
    app.run_polling()


if __name__ == "__main__":
    main()
