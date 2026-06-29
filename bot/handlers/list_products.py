"""
handlers/list_products.py
نمایش لیست محصولات با دکمه‌های inline برای رفتن به ویرایش/حذف.
"""
from telebot import TeleBot
from telebot.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

from config import is_admin
from product_store import list_products


def register_list_handlers(bot: TeleBot):

    @bot.message_handler(commands=["list"])
    def cmd_list(message: Message):
        if not is_admin(message.from_user.id):
            bot.reply_to(message, "⛔️ این دستور فقط برای ادمین‌هاست.")
            return

        products = list_products()
        if not products:
            bot.reply_to(message, "هنوز هیچ محصولی ثبت نشده. با /add شروع کن.")
            return

        for p in products:
            status = "✅ فعال" if p.get("is_active", True) else "🚫 غیرفعال"
            stock = f"{p['stock_count']} عدد" if p.get("stock_count", 0) > 0 else "ناموجود"
            text = (
                f"🆔 {p['id']}\n"
                f"📌 {p['title']}\n"
                f"💰 {p['price']:,} تومان\n"
                f"🏷 {p['category']}\n"
                f"📦 {stock}\n"
                f"وضعیت: {status}"
            )
            kb = InlineKeyboardMarkup()
            kb.row(
                InlineKeyboardButton("✏️ ویرایش", callback_data=f"edit:{p['id']}"),
                InlineKeyboardButton("🗑 حذف", callback_data=f"del:{p['id']}"),
            )
            kb.row(
                InlineKeyboardButton("📦 کم کردن موجودی", callback_data=f"stockdec:{p['id']}"),
            )
            bot.send_message(message.chat.id, text, reply_markup=kb)
