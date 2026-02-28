import asyncio
import time
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from playwright.async_api import async_playwright

TOKEN = "8416883655:AAHXQBlS383CbgiaTdSV_aTpc0YdaRnM9c0"

user_cooldown = {}
COOLDOWN_TIME = 15


# ===============================
async def check_email(email, send_photo_callback):
    url = f"https://vi.emailfake.com//{email}"

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        try:
            await page.goto(url, timeout=60000)
            await page.wait_for_timeout(5000)

            content = await page.content()
            text = content.lower()

            keywords = [
                "access deactivated",
                "deactivating your access",
                "violated our policies",
                "account has been deactivated",
                "not permitted under our policies",
                "openai team"
            ]

            detected = any(k in text for k in keywords)

            # ===== Screenshot nếu khóa
            if detected:
                screenshot_path = f"screenshot_{email.replace('@','_')}.png"
                await page.screenshot(path=screenshot_path, full_page=True)
                await send_photo_callback(screenshot_path)

            await browser.close()
            return detected

        except Exception as e:
            await browser.close()
            print("ERROR:", e)
            return None


# ===============================
async def scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    now = time.time()

    # ===== Anti spam
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

    emails = context.args[:3]  # Giới hạn 3 email
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

        async def send_photo(path):
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=open(path, "rb"),
                caption=f"📸 Inbox của {email}"
            )

        result = await check_email(email, send_photo)

        if result is True:
            locked.append(email)
        elif result is False:
            safe.append(email)
        else:
            errors.append(email)

    # ===============================
    # Tạo kết quả đẹp
    # ===============================
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
        result_text += "⚠️ LỖI KHÔNG ĐỌC ĐƯỢC:\n"
        for e in errors:
            result_text += f"   • {e}\n"

    if not locked and not safe:
        result_text += "Không có kết quả"

    await status.edit_text(result_text)


# ===============================
def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("scan", scan))

    print("BOT FINAL ĐANG CHẠY...")
    app.run_polling()


if __name__ == "__main__":
    main()