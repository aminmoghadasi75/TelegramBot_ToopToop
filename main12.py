from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import logging
import asyncio

#new eddit

# تنظیمات لاگ‌گیری
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# اطلاعات بات و کانال‌ها
BOT_TOKEN = "8164630657:AAGcf35y3u6SbHDegxZCVKtKSNsL4B7OS0g"
STORAGE_CHANNEL = -1002463367628  # جایگزین با آیدی عددی کانال خصوصی
REQUIRED_CHANNELS = ["@Rock_Guys", "@Ami9music"]

# تابع بررسی عضویت کاربر
async def get_unjoined_channels(user_id: int, context: ContextTypes.DEFAULT_TYPE):
    unjoined_channels = []
    for channel in REQUIRED_CHANNELS:
        try:
            member = await context.bot.get_chat_member(chat_id=channel, user_id=user_id)
            if member.status not in ["member", "administrator", "creator"]:
                unjoined_channels.append(channel)
        except Exception as e:
            logger.error(f"خطا در بررسی عضویت: {e}")
            unjoined_channels.append(channel)
    return unjoined_channels

# تابع ایجاد دکمه‌های عضویت و تأیید
def get_verification_menu(unjoined_channels):
    keyboard = [[InlineKeyboardButton(f"✅ عضویت در {ch}", url=f"https://t.me/{ch[1:]}")] for ch in unjoined_channels]
    keyboard.append([InlineKeyboardButton("🔄 بررسی مجدد عضویت", callback_data="verify")])
    return InlineKeyboardMarkup(keyboard)

# ارسال محتوا به کاربر با تأخیر برای حذف آن
async def send_timed_message(user_id: int, context: ContextTypes.DEFAULT_TYPE, content_code: str):
    try:
        sent_message = await context.bot.forward_message(
            chat_id=user_id,
            from_chat_id=STORAGE_CHANNEL,
            message_id=int(content_code)
        )
        countdown_message = await context.bot.send_message(
            chat_id=user_id,
            text="⏳ این محتوا پس از ۲ دقیقه حذف خواهد شد!"
        )
        
        # Run the sleep asynchronously without blocking other requests
        await asyncio.sleep(120)
        
        await context.bot.delete_message(chat_id=user_id, message_id=sent_message.message_id)
        await context.bot.delete_message(chat_id=user_id, message_id=countdown_message.message_id)
    except Exception as e:
        logger.error(f"خطا در ارسال محتوا: {e}")
        await context.bot.send_message(chat_id=user_id, text="⚠️ خطایی در دریافت محتوا رخ داد. لطفاً بعداً تلاش کنید.")

# دستور /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    args = context.args if context.args else []
    content_code = args[0] if args and args[0].isdigit() else None

    unjoined_channels = await get_unjoined_channels(user.id, context)
    if not unjoined_channels:
        if content_code:
            asyncio.create_task(send_timed_message(user.id, context, content_code))  # Run independently
            await update.message.reply_text("📩 محتوای شما در حال ارسال است...")
        else:
            await update.message.reply_text("✅ خوش آمدید! برای دریافت رسانه، از لینک‌های محتوایی استفاده کنید.")
    else:
        await update.message.reply_text(
            "⚠️ برای دسترسی به محتوا، ابتدا در کانال‌های زیر عضو شوید:",
            reply_markup=get_verification_menu(unjoined_channels)
        )

# بررسی عضویت از طریق دکمه تأیید
async def verify_membership(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    
    unjoined_channels = await get_unjoined_channels(query.from_user.id, context)
    if not unjoined_channels:
        await query.edit_message_text("✅ عضویت شما تأیید شد! اکنون می‌توانید به محتوای رسانه‌ای دسترسی داشته باشید.")
    else:
        await query.edit_message_text(
            "⚠️ شما هنوز در تمام کانال‌ها عضو نشده‌اید. لطفاً ابتدا عضو شوید:",
            reply_markup=get_verification_menu(unjoined_channels)
        )

# راه‌اندازی ربات
def main():
    application = Application.builder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(verify_membership, pattern="verify"))
    
    application.run_polling()

if __name__ == '__main__':
    main()
