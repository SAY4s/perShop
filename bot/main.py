"""
main.py
نقطه ورود بات perShop. این فایل رو روی سرور/کامپیوتر همیشه‌روشن اجرا کن:
    python main.py
"""
from telebot import TeleBot
from telebot.types import WebAppInfo, MenuButtonWebApp, InlineKeyboardMarkup, InlineKeyboardButton

from config import BOT_TOKEN, SITE_URL
from handlers.add_product import register_add_product_handlers
from handlers.list_products import register_list_handlers
from handlers.edit_delete_product import register_edit_delete_handlers
from handlers.order import register_order_handlers

if not BOT_TOKEN:
    raise SystemExit("❌ BOT_TOKEN در فایل .env تنظیم نشده. اول config رو کامل کن.")

bot = TeleBot(BOT_TOKEN, parse_mode=None)

register_order_handlers(bot)          # /start و order_<id>
register_add_product_handlers(bot)    # /add
register_list_handlers(bot)           # /list
register_edit_delete_handlers(bot)    # ویرایش و حذف از روی لیست


def setup_menu_button():
    """
    دکمه ثابت کنار باکس پیام رو به یک Mini App وصل می‌کنه که سایت رو
    بدون خروج از تلگرام باز می‌کنه. اگه SITE_URL تنظیم نشده باشه، این کار رد می‌شه.
    """
    if not SITE_URL:
        print("⚠️ SITE_URL در .env تنظیم نشده؛ دکمه منوی Mini App غیرفعال ماند.")
        return
    try:
        bot.set_chat_menu_button(menu_button=MenuButtonWebApp(text="🛍 فروشگاه", web_app=WebAppInfo(SITE_URL)))
        print(f"✅ دکمه منوی Mini App روی {SITE_URL} فعال شد.")
    except Exception as e:
        print(f"⚠️ نصب دکمه منو ناموفق بود: {e}")


@bot.message_handler(commands=["shop"])
def cmd_shop(message):
    if not SITE_URL:
        bot.reply_to(message, "❌ آدرس فروشگاه هنوز در .env تنظیم نشده (SITE_URL).")
        return
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("🛍 باز کردن فروشگاه", web_app=WebAppInfo(SITE_URL)))
    bot.send_message(message.chat.id, "فروشگاه رو از همینجا باز کن:", reply_markup=kb)


@bot.message_handler(commands=["help"])
def cmd_help(message):
    bot.reply_to(
        message,
        "📋 دستورات ادمین:\n"
        "/add - افزودن محصول جدید\n"
        "/list - مشاهده و مدیریت محصولات\n"
        "/shop - باز کردن فروشگاه به‌صورت Mini App\n\n"
        "مشتری‌ها از دکمه 🛍 کنار باکس پیام یا دستور /shop وارد فروشگاه می‌شن."
    )


if __name__ == "__main__":
    setup_menu_button()
    print("🚀 perShop bot is running...")
    bot.infinity_polling()
