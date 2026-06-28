"""
handlers/order.py
وقتی مشتری از سایت روی دکمه خرید کلیک می‌کنه، به دیپ‌لینک
t.me/BOT_USERNAME?start=order_<id> هدایت می‌شه. این هندلر سفارش
رو می‌گیره، اطلاعات تماس مشتری رو می‌پرسه، و به ادمین‌ها فوروارد می‌کنه.
"""
from telebot import TeleBot
from telebot.types import Message

from config import ADMIN_IDS
from product_store import get_product

# state موقت: user_id -> {"product_id": ...}
_order_states = {}


def register_order_handlers(bot: TeleBot):

    @bot.message_handler(commands=["start"])
    def cmd_start(message: Message):
        args = message.text.split(maxsplit=1)
        if len(args) < 2 or not args[1].startswith("order_"):
            bot.reply_to(message, "👋 سلام! به perShop خوش اومدی.")
            return

        product_id = args[1][len("order_"):]
        product = get_product(product_id)
        if not product:
            bot.reply_to(message, "❌ این محصول دیگه موجود نیست.")
            return

        if not product.get("is_active", True) or product.get("stock_count", 0) <= 0:
            bot.reply_to(message, f"⚠️ محصول «{product['title']}» متأسفانه ناموجود است.")
            return

        _order_states[message.from_user.id] = {"product_id": product_id}
        bot.reply_to(
            message,
            f"🛒 سفارش محصول:\n"
            f"📌 {product['title']}\n"
            f"💰 {product['price']:,} تومان\n\n"
            f"برای ثبت سفارش، لطفاً شماره تماس یا آیدی تلگرامت رو همراه با توضیح بفرست "
            f"(مثلاً تعداد مدنظر یا آدرس، اگه لازمه). یک ادمین به‌زودی باهات هماهنگ می‌کنه."
        )

    @bot.message_handler(func=lambda m: m.from_user.id in _order_states)
    def receive_order_details(message: Message):
        state = _order_states.pop(message.from_user.id)
        product = get_product(state["product_id"])
        if not product:
            bot.reply_to(message, "❌ این محصول دیگه موجود نیست.")
            return

        customer = message.from_user
        customer_tag = f"@{customer.username}" if customer.username else f"id:{customer.id}"

        admin_text = (
            f"🛎 سفارش جدید!\n\n"
            f"🆔 محصول: {product['id']} - {product['title']}\n"
            f"💰 قیمت: {product['price']:,} تومان\n"
            f"👤 مشتری: {customer.first_name or ''} {customer_tag}\n"
            f"📝 توضیح/تماس مشتری:\n{message.text}\n\n"
            f"برای هماهنگی نهایی مستقیم با مشتری در ارتباط باش."
        )
        for admin_id in ADMIN_IDS:
            try:
                bot.send_message(admin_id, admin_text)
            except Exception:
                pass

        bot.reply_to(
            message,
            "✅ سفارشت ثبت شد و برای ادمین فرستاده شد.\n"
            "به‌زودی برای تکمیل خرید باهات تماس گرفته می‌شه. ممنون از خریدت از perShop 🌟"
        )
