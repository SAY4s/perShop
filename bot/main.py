"""
main.py
نقطه ورود بات perShop. این فایل رو روی سرور/کامپیوتر همیشه‌روشن اجرا کن:
    python main.py
"""
from telebot import TeleBot

from config import BOT_TOKEN
from handlers.add_product import register_add_product_handlers
from handlers.list_products import register_list_handlers
from handlers.edit_delete_product import register_edit_delete_handlers
from handlers.order import register_order_handlers

if not BOT_TOKEN:
    raise SystemExit("❌ BOT_TOKEN در فایل .env تنظیم نشده. اول config رو کامل کن.")

bot = TeleBot(BOT_TOKEN, parse_mode=None)

register_order_handlers(bot)          # /start و order_<id>
register_add_product_handlers(bot)    # /addproduct
register_list_handlers(bot)           # /listproducts
register_edit_delete_handlers(bot)    # ویرایش و حذف از روی لیست


@bot.message_handler(commands=["help"])
def cmd_help(message):
    bot.reply_to(
        message,
        "📋 دستورات ادمین:\n"
        "/addproduct - افزودن محصول جدید\n"
        "/listproducts - مشاهده و مدیریت محصولات\n\n"
        "مشتری‌ها از طریق دکمه خرید در سایت وارد بات می‌شن."
    )


if __name__ == "__main__":
    print("🚀 perShop bot is running...")
    bot.infinity_polling()
