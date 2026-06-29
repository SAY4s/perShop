"""
handlers/admin_orders.py
دستور /orders برای ادمین: لیست سفارش‌های در انتظار (pending) با دکمه‌ی
تأیید/رد. این جداست از /myorders که مخصوص خود مشتریه.
"""
from telebot import TeleBot
from telebot.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

from config import is_admin
import orders_store


def register_admin_orders_handlers(bot: TeleBot):

    @bot.message_handler(commands=["orders"])
    def cmd_orders(message: Message):
        if not is_admin(message.from_user.id):
            bot.reply_to(message, "⛔️ این دستور فقط برای ادمین‌هاست.")
            return

        pending = orders_store.get_orders_by_status("pending")
        if not pending:
            bot.reply_to(message, "📭 هیچ سفارش در‌انتظاری وجود نداره.")
            return

        bot.reply_to(message, f"📋 {len(pending)} سفارش در انتظار تأیید:")
        for o in pending:
            text = (
                f"🆔 سفارش {o['order_id']}\n"
                f"📌 {o['product_title']}\n"
                f"💰 {o['price']:,} تومان\n"
                f"👤 {o['customer_tag']}\n"
                f"📝 {o['note']}\n"
                f"🕒 {o['created_at']}"
            )
            kb = InlineKeyboardMarkup()
            kb.row(
                InlineKeyboardButton("✅ تأیید نهایی", callback_data=f"orderconfirm:{o['order_id']}"),
                InlineKeyboardButton("❌ رد سفارش", callback_data=f"orderreject:{o['order_id']}"),
            )
            bot.send_message(message.chat.id, text, reply_markup=kb)
