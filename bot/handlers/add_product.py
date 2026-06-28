"""
handlers/add_product.py
فلوی مرحله‌ای (state machine) برای افزودن محصول جدید توسط ادمین.
"""
from telebot import TeleBot
from telebot.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

from config import is_admin
from github_client import load_products, upload_image
from product_store import add_product

# state موقت در حافظه برای هر کاربر؛ چون فقط ادمین‌ها ازش استفاده می‌کنن، حجمش کمه
_user_states = {}

STEP_TITLE = "title"
STEP_DESCRIPTION = "description"
STEP_PRICE = "price"
STEP_CATEGORY = "category"
STEP_STOCK = "stock"
STEP_IMAGE = "image"


def register_add_product_handlers(bot: TeleBot):

    @bot.message_handler(commands=["addproduct"])
    def start_add_product(message: Message):
        if not is_admin(message.from_user.id):
            bot.reply_to(message, "⛔️ این دستور فقط برای ادمین‌هاست.")
            return
        _user_states[message.from_user.id] = {"step": STEP_TITLE, "data": {}}
        bot.reply_to(message, "📦 بسیار خوب! بریم محصول جدید بسازیم.\n\nعنوان محصول رو بفرست:")

    @bot.message_handler(func=lambda m: m.from_user.id in _user_states and _user_states[m.from_user.id]["step"] == STEP_TITLE)
    def step_title(message: Message):
        state = _user_states[message.from_user.id]
        state["data"]["title"] = message.text.strip()
        state["step"] = STEP_DESCRIPTION
        bot.reply_to(message, "توضیحات محصول رو بنویس:")

    @bot.message_handler(func=lambda m: m.from_user.id in _user_states and _user_states[m.from_user.id]["step"] == STEP_DESCRIPTION)
    def step_description(message: Message):
        state = _user_states[message.from_user.id]
        state["data"]["description"] = message.text.strip()
        state["step"] = STEP_PRICE
        bot.reply_to(message, "قیمت محصول رو به تومان وارد کن (فقط عدد):")

    @bot.message_handler(func=lambda m: m.from_user.id in _user_states and _user_states[m.from_user.id]["step"] == STEP_PRICE)
    def step_price(message: Message):
        state = _user_states[message.from_user.id]
        text = message.text.strip().replace(",", "")
        if not text.isdigit():
            bot.reply_to(message, "⚠️ لطفاً فقط عدد وارد کن. مثال: 150000")
            return
        state["data"]["price"] = int(text)
        state["step"] = STEP_CATEGORY

        data, _ = load_products()
        categories = data.get("categories", [])
        kb = InlineKeyboardMarkup()
        for cat in categories:
            kb.add(InlineKeyboardButton(cat, callback_data=f"cat:{cat}"))
        kb.add(InlineKeyboardButton("➕ دسته جدید", callback_data="cat:__new__"))
        bot.reply_to(message, "دسته‌بندی محصول رو انتخاب کن:", reply_markup=kb)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("cat:"))
    def on_category_chosen(call):
        user_id = call.from_user.id
        if user_id not in _user_states or _user_states[user_id]["step"] != STEP_CATEGORY:
            bot.answer_callback_query(call.id)
            return

        chosen = call.data.split(":", 1)[1]
        state = _user_states[user_id]

        if chosen == "__new__":
            state["step"] = "category_new"
            bot.answer_callback_query(call.id)
            bot.send_message(user_id, "اسم دسته‌بندی جدید رو بنویس:")
            return

        state["data"]["category"] = chosen
        state["step"] = STEP_STOCK
        bot.answer_callback_query(call.id)
        bot.send_message(user_id, f"دسته انتخاب شد: {chosen}\n\nتعداد موجودی رو وارد کن (فقط عدد، صفر یعنی ناموجود):")

    @bot.message_handler(func=lambda m: m.from_user.id in _user_states and _user_states[m.from_user.id]["step"] == "category_new")
    def step_new_category(message: Message):
        state = _user_states[message.from_user.id]
        state["data"]["category"] = message.text.strip()
        state["step"] = STEP_STOCK
        bot.reply_to(message, "تعداد موجودی رو وارد کن (فقط عدد، صفر یعنی ناموجود):")

    @bot.message_handler(func=lambda m: m.from_user.id in _user_states and _user_states[m.from_user.id]["step"] == STEP_STOCK)
    def step_stock(message: Message):
        state = _user_states[message.from_user.id]
        text = message.text.strip()
        if not text.isdigit():
            bot.reply_to(message, "⚠️ لطفاً فقط عدد وارد کن. مثال: 10")
            return
        state["data"]["stock_count"] = int(text)
        state["step"] = STEP_IMAGE
        bot.reply_to(message, "📷 حالا عکس محصول رو بفرست:")

    @bot.message_handler(content_types=["photo"], func=lambda m: m.from_user.id in _user_states and _user_states[m.from_user.id]["step"] == STEP_IMAGE)
    def step_image(message: Message):
        state = _user_states.pop(message.from_user.id)
        d = state["data"]

        bot.reply_to(message, "⏳ در حال آپلود عکس و ثبت محصول روی گیت‌هاب...")

        file_id = message.photo[-1].file_id
        file_info = bot.get_file(file_id)
        downloaded = bot.download_file(file_info.file_path)

        from product_store import generate_id
        from github_client import load_products as _lp
        data_now, _ = _lp()
        next_id = generate_id(data_now["products"])
        filename = f"{next_id}.jpg"

        rel_path = upload_image(filename, downloaded, f"chore: upload image for {next_id}")
        image_url_relative = f"./{rel_path.split('site/', 1)[-1]}" if "site/" in rel_path else f"./{rel_path}"

        product = add_product(
            title=d["title"],
            description=d["description"],
            price=d["price"],
            category=d["category"],
            image_url=image_url_relative,
            stock_count=d["stock_count"],
            commit_actor=message.from_user.username or str(message.from_user.id),
        )

        bot.send_message(
            message.chat.id,
            f"✅ محصول با موفقیت ثبت شد!\n\n"
            f"🆔 {product['id']}\n"
            f"📌 {product['title']}\n"
            f"💰 {product['price']:,} تومان\n"
            f"🏷 {product['category']}\n"
            f"📦 موجودی: {product['stock_count']}\n\n"
            f"سایت تا چند دقیقه دیگه آپدیت می‌شه."
        )
