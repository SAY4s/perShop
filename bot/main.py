"""
main.py
نقطه ورود بات perShop. این فایل رو روی سرور/کامپیوتر همیشه‌روشن اجرا کن:
    python main.py
"""
import threading
import time

from telebot import TeleBot
from telebot.types import WebAppInfo, MenuButtonWebApp, InlineKeyboardMarkup, InlineKeyboardButton

from config import BOT_TOKEN, SITE_URL, is_admin
from handlers.add_product import register_add_product_handlers
from handlers.list_products import register_list_handlers
from handlers.edit_delete_product import register_edit_delete_handlers
from handlers.stock import register_stock_handlers
from handlers.order import register_order_handlers
from handlers.admin_orders import register_admin_orders_handlers
from handlers.my_orders import register_my_orders_handlers
from product_store import get_stats
import orders_store

if not BOT_TOKEN:
    raise SystemExit("❌ BOT_TOKEN در فایل .env تنظیم نشده. اول config رو کامل کن.")

bot = TeleBot(BOT_TOKEN, parse_mode=None)

register_order_handlers(bot)          # /start و order_<id>
register_add_product_handlers(bot)    # /add
register_list_handlers(bot)           # /list
register_edit_delete_handlers(bot)    # ویرایش و حذف از روی لیست
register_stock_handlers(bot)          # کم کردن موجودی دستی
register_admin_orders_handlers(bot)   # /orders (ادمین)
register_my_orders_handlers(bot)      # /myorders (مشتری)


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


def abandoned_orders_watcher():
    """
    هر چند دقیقه یک‌بار، سفارش‌های incomplete/pending قدیمی رو که مشتری
    دیگه پاسخ نداده، خودکار «منصرف‌شده» علامت می‌زنه. این ترد جدا از
    polling اصلی بات اجرا می‌شه و کاری به دریافت پیام‌ها نداره.
    """
    while True:
        try:
            expired = orders_store.expire_abandoned_orders()
            if expired:
                print(f"⏳ {len(expired)} سفارش به‌خاطر بی‌پاسخی خودکار لغو شد.")
        except Exception as e:
            print(f"⚠️ خطا در بررسی سفارش‌های رهاشده: {e}")
        time.sleep(300)  # هر ۵ دقیقه


@bot.message_handler(commands=["shop"])
def cmd_shop(message):
    if not SITE_URL:
        bot.reply_to(message, "❌ آدرس فروشگاه هنوز در .env تنظیم نشده (SITE_URL).")
        return
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("🛍 باز کردن فروشگاه", web_app=WebAppInfo(SITE_URL)))
    bot.send_message(message.chat.id, "فروشگاه رو از همینجا باز کن:", reply_markup=kb)


def _simulate_command(call, command_text):
    """ یک پیام مصنوعی می‌سازه تا انگار ادمین خودش دستور رو تایپ کرده. """
    from telebot.types import Message
    import time
    fake = Message(
        message_id=call.message.message_id,
        from_user=call.from_user,
        date=int(time.time()),
        chat=call.message.chat,
        content_type="text",
        options={},
        json_string="",
    )
    fake.text = command_text
    bot.process_new_messages([fake])


@bot.callback_query_handler(func=lambda c: c.data == "quickadd")
def on_quickadd(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "⛔️ دسترسی نداری.")
        return
    bot.answer_callback_query(call.id)
    _simulate_command(call, "/add")


@bot.callback_query_handler(func=lambda c: c.data == "quicklist")
def on_quicklist(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "⛔️ دسترسی نداری.")
        return
    bot.answer_callback_query(call.id)
    _simulate_command(call, "/list")


@bot.message_handler(commands=["stats"])
def cmd_stats(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "⛔️ این دستور فقط برای ادمین‌هاست.")
        return

    s = get_stats()
    cat_lines = "\n".join(f"   • {cat}: {count}" for cat, count in s["per_category"].items()) or "   —"

    text = (
        "📊 آمار فروشگاه perShop\n\n"
        f"📦 کل محصولات: {s['total']}\n"
        f"✅ فعال: {s['active']}  |  🚫 غیرفعال: {s['inactive']}\n"
        f"⚠️ ناموجود (از فعال‌ها): {s['out_of_stock']}\n"
        f"🏷 تعداد دسته‌بندی: {s['categories_count']}\n"
        f"💰 ارزش کل موجودی: {s['total_stock_value']:,} تومان\n\n"
        f"📁 محصولات فعال به تفکیک دسته:\n{cat_lines}\n\n"
        f"🛎 سفارش‌های امروز: {orders_store.count_orders_today()}\n"
        f"🛎 کل سفارش‌های ثبت‌شده: {orders_store.count_orders_total()}\n"
        f"   🟡 نصفه‌نیمه: {orders_store.count_by_status('incomplete')}\n"
        f"   🔵 در انتظار: {orders_store.count_by_status('pending')}\n"
        f"   ✅ نهایی‌شده: {orders_store.count_by_status('confirmed')}\n"
        f"   🚫 منصرف/رد‌شده: {orders_store.count_by_status('cancelled')}"
    )
    bot.reply_to(message, text)


@bot.message_handler(commands=["help"])
def cmd_help(message):
    if is_admin(message.from_user.id):
        bot.reply_to(
            message,
            "📋 دستورات ادمین:\n"
            "/add - افزودن محصول جدید\n"
            "/list - مشاهده و مدیریت محصولات (و کم کردن موجودی)\n"
            "/orders - بررسی سفارش‌های در انتظار تأیید\n"
            "/stats - آمار فروشگاه و سفارش‌ها\n"
            "/shop - باز کردن فروشگاه به‌صورت Mini App\n\n"
            "مشتری‌ها از دکمه 🛍 کنار باکس پیام یا دستور /shop وارد فروشگاه می‌شن "
            "و با /myorders تاریخچه‌ی سفارش‌های خودشون رو می‌بینن."
        )
    else:
        bot.reply_to(
            message,
            "👋 به perShop خوش اومدی!\n"
            "/shop - باز کردن فروشگاه\n"
            "/myorders - دیدن تاریخچه‌ی سفارش‌هات"
        )


if __name__ == "__main__":
    setup_menu_button()

    watcher_thread = threading.Thread(target=abandoned_orders_watcher, daemon=True)
    watcher_thread.start()

    print("🚀 perShop bot is running...")
    # timeout بالاتر برای هندشیک TLS کندتر (به‌خاطر VPN/پراکسی) و
    # long_polling_timeout پایین‌تر برای تجدید سریع‌تر اتصال در صورت قطعی.
    # interval کوچک یعنی بعد از هر خطا خیلی سریع دوباره تلاش می‌کنه (به‌جای توقف).
    bot.infinity_polling(timeout=30, long_polling_timeout=15, interval=2)
