"""
handlers/order.py
وقتی مشتری از سایت روی دکمه خرید کلیک می‌کنه، به دیپ‌لینک
t.me/BOT_USERNAME?start=order_<id> هدایت می‌شه. این هندلر سفارش رو با
وضعیت «incomplete» می‌سازه، توضیح/تماس مشتری رو می‌گیره (وضعیت → pending)،
و به ادمین‌ها با دکمه‌ی تأیید/رد فوروارد می‌کنه.

همچنین /start ساده (بدون پارامتر سفارش) یک دکمه برای باز کردن
فروشگاه به‌صورت Mini App نشون می‌ده.
"""
from telebot import TeleBot
from telebot.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo, CallbackQuery

from config import ADMIN_IDS, SITE_URL, is_admin
from product_store import get_product
import orders_store

# state موقت: user_id -> order_id (سفارش incomplete‌ای که منتظر توضیح مشتریه)
_awaiting_note = {}


def register_order_handlers(bot: TeleBot):

    @bot.message_handler(commands=["start"])
    def cmd_start(message: Message):
        args = message.text.split(maxsplit=1)
        if len(args) < 2 or not args[1].startswith("order_"):
            kb = None
            if SITE_URL:
                kb = InlineKeyboardMarkup()
                kb.add(InlineKeyboardButton("🛍 باز کردن فروشگاه", web_app=WebAppInfo(SITE_URL)))
            bot.send_message(
                message.chat.id,
                "👋 سلام! به perShop خوش اومدی.\n"
                + ("برای دیدن محصولات روی دکمه‌ی زیر بزن:" if SITE_URL else "فعلاً آدرس فروشگاه تنظیم نشده."),
                reply_markup=kb,
            )
            return

        product_id = args[1][len("order_"):]
        product = get_product(product_id)
        if not product:
            bot.reply_to(message, "❌ این محصول دیگه موجود نیست.")
            return

        if not product.get("is_active", True) or product.get("stock_count", 0) <= 0:
            bot.reply_to(message, f"⚠️ محصول «{product['title']}» متأسفانه ناموجود است.")
            return

        customer = message.from_user
        customer_tag = f"@{customer.username}" if customer.username else f"id:{customer.id}"

        order_id = orders_store.create_incomplete_order(
            product_id=product["id"],
            product_title=product["title"],
            price=product["price"],
            customer_id=customer.id,
            customer_tag=customer_tag,
        )
        _awaiting_note[customer.id] = order_id

        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("❌ انصراف از این سفارش", callback_data=f"ordercancel:{order_id}"))
        bot.reply_to(
            message,
            f"🛒 سفارش محصول:\n"
            f"📌 {product['title']}\n"
            f"💰 {product['price']:,} تومان\n\n"
            f"برای ثبت سفارش، لطفاً شماره تماس یا آیدی تلگرامت رو همراه با توضیح بفرست "
            f"(مثلاً تعداد مدنظر یا آدرس، اگه لازمه). یک ادمین به‌زودی باهات هماهنگ می‌کنه.",
            reply_markup=kb,
        )

    @bot.callback_query_handler(func=lambda c: c.data.startswith("ordercancel:"))
    def on_customer_cancel(call: CallbackQuery):
        order_id = call.data.split(":", 1)[1]
        order = orders_store.get_order(order_id)
        if not order or order["customer_id"] != call.from_user.id:
            bot.answer_callback_query(call.id, "❌ این سفارش پیدا نشد.")
            return
        if order["status"] in ("confirmed", "cancelled"):
            bot.answer_callback_query(call.id, "این سفارش قبلاً بسته شده.")
            return

        orders_store.set_status(order_id, "cancelled")
        _awaiting_note.pop(call.from_user.id, None)
        bot.answer_callback_query(call.id, "سفارش لغو شد.")
        bot.edit_message_text(
            f"🚫 سفارش «{order['product_title']}» توسط خودت لغو شد.",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
        )

    @bot.message_handler(func=lambda m: m.from_user.id in _awaiting_note)
    def receive_order_details(message: Message):
        customer = message.from_user
        order_id = _awaiting_note.pop(customer.id)
        order = orders_store.mark_pending(order_id, message.text)
        if not order:
            bot.reply_to(message, "❌ این سفارش دیگه معتبر نیست.")
            return

        admin_text = (
            f"🛎 سفارش جدید! ({order['order_id']})\n\n"
            f"🆔 محصول: {order['product_id']} - {order['product_title']}\n"
            f"💰 قیمت: {order['price']:,} تومان\n"
            f"👤 مشتری: {customer.first_name or ''} {order['customer_tag']}\n"
            f"📝 توضیح/تماس مشتری:\n{order['note']}"
        )
        admin_kb = InlineKeyboardMarkup()
        admin_kb.row(
            InlineKeyboardButton("✅ تأیید نهایی", callback_data=f"orderconfirm:{order['order_id']}"),
            InlineKeyboardButton("❌ رد سفارش", callback_data=f"orderreject:{order['order_id']}"),
        )
        for admin_id in ADMIN_IDS:
            try:
                bot.send_message(admin_id, admin_text, reply_markup=admin_kb)
            except Exception:
                pass

        bot.reply_to(
            message,
            "✅ سفارشت ثبت شد و برای ادمین فرستاده شد.\n"
            "به‌زودی برای تکمیل خرید باهات تماس گرفته می‌شه. ممنون از خریدت از perShop 🌟\n\n"
            "وضعیت سفارش‌هات رو هر وقت خواستی با /myorders ببین."
        )

    @bot.callback_query_handler(func=lambda c: c.data.startswith("orderconfirm:") or c.data.startswith("orderreject:"))
    def on_admin_decision(call: CallbackQuery):
        if not is_admin(call.from_user.id):
            bot.answer_callback_query(call.id, "⛔️ دسترسی نداری.")
            return

        action, order_id = call.data.split(":", 1)
        order = orders_store.get_order(order_id)
        if not order:
            bot.answer_callback_query(call.id, "❌ سفارش پیدا نشد.")
            return

        new_status = "confirmed" if action == "orderconfirm" else "cancelled"
        orders_store.set_status(order_id, new_status)

        label = "✅ تأیید شد" if new_status == "confirmed" else "❌ رد شد"
        bot.answer_callback_query(call.id, label)
        try:
            bot.edit_message_text(
                call.message.text + f"\n\n— {label} توسط {call.from_user.first_name or call.from_user.username}",
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
            )
        except Exception:
            pass

        # اطلاع به مشتری
        try:
            if new_status == "confirmed":
                bot.send_message(
                    order["customer_id"],
                    f"🎉 سفارش «{order['product_title']}» تأیید شد! به‌زودی برای تکمیل خرید باهات هماهنگ می‌شه."
                )
            else:
                bot.send_message(
                    order["customer_id"],
                    f"متأسفانه سفارش «{order['product_title']}» توسط فروشگاه رد شد. می‌تونی دوباره سفارش بدی یا با ادمین در ارتباط باشی."
                )
        except Exception:
            pass
