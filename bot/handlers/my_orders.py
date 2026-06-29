"""
handlers/my_orders.py
دستور /myorders: مشتری تاریخچه‌ی کامل سفارش‌های خودش رو می‌بینه -
نهایی‌شده، در‌انتظار، نصفه‌نیمه (incomplete)، و منصرف‌شده.
"""
from telebot import TeleBot
from telebot.types import Message

import orders_store

STATUS_LABELS = {
    "incomplete": "🟡 نصفه‌نیمه (توضیح نفرستادی)",
    "pending": "🔵 در انتظار تأیید ادمین",
    "confirmed": "✅ نهایی‌شده",
    "cancelled": "🚫 منصرف‌شده / رد شده",
}


def register_my_orders_handlers(bot: TeleBot):

    @bot.message_handler(commands=["myorders"])
    def cmd_my_orders(message: Message):
        orders = orders_store.get_orders_by_customer(message.from_user.id)
        if not orders:
            bot.reply_to(message, "📭 هنوز هیچ سفارشی ثبت نکردی.")
            return

        lines = [f"🧾 تاریخچه‌ی سفارش‌های تو ({len(orders)} مورد):\n"]
        for o in orders:
            label = STATUS_LABELS.get(o["status"], o["status"])
            lines.append(
                f"——————————\n"
                f"📌 {o['product_title']}\n"
                f"💰 {o['price']:,} تومان\n"
                f"وضعیت: {label}\n"
                f"🕒 {o['created_at'][:16].replace('T', ' ')}"
            )
        bot.reply_to(message, "\n".join(lines))
