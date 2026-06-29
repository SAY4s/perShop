"""
handlers/stock.py
وقتی ادمین فروشی رو نهایی می‌کنه (یا هر دلیل دیگه)، می‌تونه موجودی محصول رو
دستی کم کنه - یا با یک کلیک «۱-» یا با وارد کردن عدد دلخواه. این کاملاً
مستقل از فلوی سفارش‌گیری مشتری‌هاست؛ موجودی هیچ‌وقت خودکار کم نمی‌شه.
"""
from telebot import TeleBot
from telebot.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from config import is_admin
from product_store import get_product, decrease_stock

# state موقت برای گرفتن عدد دلخواه: user_id -> product_id
_awaiting_custom_amount = {}


def register_stock_handlers(bot: TeleBot):

    @bot.callback_query_handler(func=lambda c: c.data.startswith("stockdec:"))
    def on_stock_decrease_clicked(call: CallbackQuery):
        if not is_admin(call.from_user.id):
            bot.answer_callback_query(call.id, "⛔️ دسترسی نداری.")
            return
        product_id = call.data.split(":", 1)[1]
        product = get_product(product_id)
        if not product:
            bot.answer_callback_query(call.id, "❌ محصول پیدا نشد.")
            return

        kb = InlineKeyboardMarkup()
        kb.row(
            InlineKeyboardButton("➖ ۱ تا کم کن", callback_data=f"stockdec1:{product_id}"),
            InlineKeyboardButton("🔢 عدد دلخواه", callback_data=f"stockdeccustom:{product_id}"),
        )
        bot.answer_callback_query(call.id)
        bot.send_message(
            call.from_user.id,
            f"📦 موجودی فعلی «{product['title']}»: {product['stock_count']} عدد\nچقدر کم بشه؟",
            reply_markup=kb,
        )

    @bot.callback_query_handler(func=lambda c: c.data.startswith("stockdec1:"))
    def on_decrease_by_one(call: CallbackQuery):
        if not is_admin(call.from_user.id):
            bot.answer_callback_query(call.id, "⛔️ دسترسی نداری.")
            return
        product_id = call.data.split(":", 1)[1]
        updated = decrease_stock(product_id, 1, commit_actor=call.from_user.username or str(call.from_user.id))
        bot.answer_callback_query(call.id)
        if updated:
            bot.send_message(
                call.from_user.id,
                f"✅ موجودی «{updated['title']}» یک واحد کم شد.\n📦 موجودی فعلی: {updated['stock_count']} عدد",
            )
        else:
            bot.send_message(call.from_user.id, "❌ محصول پیدا نشد.")

    @bot.callback_query_handler(func=lambda c: c.data.startswith("stockdeccustom:"))
    def on_decrease_custom_prompt(call: CallbackQuery):
        if not is_admin(call.from_user.id):
            bot.answer_callback_query(call.id, "⛔️ دسترسی نداری.")
            return
        product_id = call.data.split(":", 1)[1]
        _awaiting_custom_amount[call.from_user.id] = product_id
        bot.answer_callback_query(call.id)
        bot.send_message(call.from_user.id, "چه تعداد از موجودی کم بشه؟ یک عدد بفرست:")

    @bot.message_handler(func=lambda m: m.from_user.id in _awaiting_custom_amount)
    def on_custom_amount_received(message: Message):
        product_id = _awaiting_custom_amount.pop(message.from_user.id)
        text = message.text.strip()
        if not text.isdigit() or int(text) <= 0:
            bot.reply_to(message, "⚠️ لطفاً یک عدد مثبت بفرست. دوباره از /list شروع کن.")
            return
        amount = int(text)
        updated = decrease_stock(product_id, amount, commit_actor=message.from_user.username or str(message.from_user.id))
        if updated:
            bot.reply_to(
                message,
                f"✅ موجودی «{updated['title']}» به‌اندازه‌ی {amount} عدد کم شد.\n📦 موجودی فعلی: {updated['stock_count']} عدد",
            )
        else:
            bot.reply_to(message, "❌ محصول پیدا نشد.")
