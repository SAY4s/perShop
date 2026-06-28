"""
handlers/edit_delete_product.py
ویرایش فیلدهای یک محصول و حذف/غیرفعال‌سازی آن.
"""
from telebot import TeleBot
from telebot.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from config import is_admin
from product_store import get_product, update_product_field, delete_product, deactivate_product

# state موقت برای ویرایش: user_id -> {"product_id": ..., "field": ...}
_edit_states = {}

FIELD_LABELS = {
    "title": "عنوان",
    "description": "توضیحات",
    "price": "قیمت",
    "stock_count": "موجودی",
    "category": "دسته‌بندی",
}


def register_edit_delete_handlers(bot: TeleBot):

    @bot.callback_query_handler(func=lambda c: c.data.startswith("edit:"))
    def on_edit_clicked(call: CallbackQuery):
        if not is_admin(call.from_user.id):
            bot.answer_callback_query(call.id, "⛔️ دسترسی نداری.")
            return
        product_id = call.data.split(":", 1)[1]
        kb = InlineKeyboardMarkup()
        for field, label in FIELD_LABELS.items():
            kb.add(InlineKeyboardButton(label, callback_data=f"editfield:{product_id}:{field}"))
        bot.answer_callback_query(call.id)
        bot.send_message(call.from_user.id, f"کدوم فیلد محصول {product_id} رو می‌خوای ویرایش کنی؟", reply_markup=kb)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("editfield:"))
    def on_field_chosen(call: CallbackQuery):
        _, product_id, field = call.data.split(":")
        _edit_states[call.from_user.id] = {"product_id": product_id, "field": field}
        bot.answer_callback_query(call.id)
        bot.send_message(call.from_user.id, f"مقدار جدید برای «{FIELD_LABELS.get(field, field)}» رو بفرست:")

    @bot.message_handler(func=lambda m: m.from_user.id in _edit_states)
    def on_new_value(message: Message):
        state = _edit_states.pop(message.from_user.id)
        product_id, field = state["product_id"], state["field"]
        value = message.text.strip()

        if field in ("price", "stock_count"):
            if not value.replace(",", "").isdigit():
                bot.reply_to(message, "⚠️ این فیلد باید فقط عدد باشه. دوباره با /editproduct تلاش کن.")
                return
            value = int(value.replace(",", ""))

        updated = update_product_field(
            product_id, field, value,
            commit_actor=message.from_user.username or str(message.from_user.id),
        )
        if updated:
            bot.reply_to(message, f"✅ فیلد «{FIELD_LABELS.get(field, field)}» محصول {product_id} آپدیت شد.")
        else:
            bot.reply_to(message, "❌ محصول پیدا نشد.")

    @bot.callback_query_handler(func=lambda c: c.data.startswith("del:"))
    def on_delete_clicked(call: CallbackQuery):
        if not is_admin(call.from_user.id):
            bot.answer_callback_query(call.id, "⛔️ دسترسی نداری.")
            return
        product_id = call.data.split(":", 1)[1]
        kb = InlineKeyboardMarkup()
        kb.row(
            InlineKeyboardButton("🚫 فقط غیرفعال شه", callback_data=f"confirmdeactivate:{product_id}"),
            InlineKeyboardButton("🗑 حذف کامل", callback_data=f"confirmdelete:{product_id}"),
        )
        bot.answer_callback_query(call.id)
        bot.send_message(
            call.from_user.id,
            f"مطمئنی می‌خوای محصول {product_id} رو حذف کنی؟\n"
            f"«غیرفعال» یعنی از سایت پنهان می‌شه ولی دیتاش می‌مونه.\n"
            f"«حذف کامل» قابل بازگشت نیست.",
            reply_markup=kb,
        )

    @bot.callback_query_handler(func=lambda c: c.data.startswith("confirmdeactivate:"))
    def on_confirm_deactivate(call: CallbackQuery):
        product_id = call.data.split(":", 1)[1]
        deactivate_product(product_id, commit_actor=call.from_user.username or str(call.from_user.id))
        bot.answer_callback_query(call.id)
        bot.send_message(call.from_user.id, f"🚫 محصول {product_id} غیرفعال شد و از سایت پنهانه.")

    @bot.callback_query_handler(func=lambda c: c.data.startswith("confirmdelete:"))
    def on_confirm_delete(call: CallbackQuery):
        product_id = call.data.split(":", 1)[1]
        ok = delete_product(product_id, commit_actor=call.from_user.username or str(call.from_user.id))
        bot.answer_callback_query(call.id)
        if ok:
            bot.send_message(call.from_user.id, f"🗑 محصول {product_id} برای همیشه حذف شد.")
        else:
            bot.send_message(call.from_user.id, "❌ محصول پیدا نشد.")
