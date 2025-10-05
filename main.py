"""Kana Foods Telegram Bot (Customer + Admin)
------------------------------------------------
- Runs two Telegram bots in one file:
  * Customer bot (users place orders)
  * Admin bot (view orders via /orders)
- Do NOT put tokens in this file. Use environment variables or a .env file.
- Python 3.11
"""

import os
import asyncio
from typing import Dict, Any
from telegram import (
    Update,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    ConversationHandler,
    filters,
)

# Load tokens from environment variables (do NOT hard-code tokens here)
BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN")

if not BOT_TOKEN or not ADMIN_TOKEN:
    raise SystemExit("Error: BOT_TOKEN and ADMIN_TOKEN must be set as environment variables.")

# --- In-memory storage for orders ---
USER_ORDERS: Dict[int, Dict[str, Any]] = {}

# --- Product list (kept as requested) ---
PRODUCTS = {
    "P001": {"name": "Mozzorel Cheese", "price": 800},
    "P002": {"name": "Provolone Cheese", "price": 930},
    "P003": {"name": "Table Butter", "price": 240},
    "P004": {"name": "Chicken", "price": 650},
    "P005": {"name": "Breast Chicken", "price": 920},
}

# Conversation states
ASK_PRODUCT, ASK_QTY, CONFIRM_ORDER = range(3)


# === CUSTOMER BOT HANDLERS ===
def main_menu_keyboard():
    buttons = [
        [KeyboardButton("1. Browse Products")],
        [KeyboardButton("2. Place an Order")],
        [KeyboardButton("3. Track Delivery")],
        [KeyboardButton("4. Contact Support")],
    ]
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)


def product_list_text():
    lines = ["Available products:"]
    for pid, info in PRODUCTS.items():
        lines.append(f"{pid} — {info['name']} — {info['price']} birr")
    return "\n".join(lines)


async def start_customer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_first = update.effective_user.first_name or "there"
    welcome = (
        f"Hi {user_first}! 👋 Welcome to Kana Foods.\n\n"
        "I can help you order food supplies. What would you like to do today?\n\n"
        "For assistance, contact: +251 0986465604"
    )
    await update.message.reply_text(welcome, reply_markup=main_menu_keyboard())


async def handle_menu_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip().lower()
    user_id = update.effective_user.id

    if "browse" in text or text.startswith("1"):
        await update.message.reply_text(product_list_text(), reply_markup=main_menu_keyboard())
    elif "place" in text or text.startswith("2"):
        await update.message.reply_text(
            "Please send the PRODUCT ID you want to buy (e.g. P001):",
            reply_markup=ReplyKeyboardRemove(),
        )
        return ASK_PRODUCT
    elif "track" in text or text.startswith("3"):
        order = USER_ORDERS.get(user_id)
        if order:
            await update.message.reply_text(
                f"📦 Your last order:\n{PRODUCTS[order['product_id']]['name']} × {order['qty']} pcs\n"
                f"Status: {order['status']}",
                reply_markup=main_menu_keyboard(),
            )
        else:
            await update.message.reply_text("You don't have any active orders.", reply_markup=main_menu_keyboard())
    elif "contact" in text or text.startswith("4"):
        await update.message.reply_text("📞 Contact Support:\n+251 0986465604", reply_markup=main_menu_keyboard())
    else:
        await update.message.reply_text("Please choose an option from the menu.", reply_markup=main_menu_keyboard())
    return ConversationHandler.END


async def ask_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pid = update.message.text.strip().upper()
    if pid not in PRODUCTS:
        await update.message.reply_text("Invalid product ID. Try again (e.g. P001).")
        return ASK_PRODUCT
    context.user_data["order"] = {"product_id": pid}
    await update.message.reply_text(f"How many units of {PRODUCTS[pid]['name']}?")
    return ASK_QTY


async def ask_qty(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if not text.isdigit():
        await update.message.reply_text("Please send a number for quantity.")
        return ASK_QTY
    qty = int(text)
    pid = context.user_data["order"]["product_id"]
    total = PRODUCTS[pid]["price"] * qty
    context.user_data["order"]["qty"] = qty
    context.user_data["order"]["total"] = total
    await update.message.reply_text(
        f"Confirm order:\n{PRODUCTS[pid]['name']} × {qty}\nTotal: {total} birr\n\nType 'yes' to confirm or 'no' to cancel."
    )
    return CONFIRM_ORDER


async def confirm_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip().lower()
    user_id = update.effective_user.id
    order = context.user_data.get("order")

    if text in ["yes", "y"]:
        USER_ORDERS[user_id] = {
            **order,
            "status": "Confirmed – preparing for dispatch",
            "customer": update.effective_user.first_name,
        }
        await update.message.reply_text("✅ Order placed! We’ll contact you soon.", reply_markup=main_menu_keyboard())
    else:
        await update.message.reply_text("❌ Order cancelled.", reply_markup=main_menu_keyboard())

    context.user_data.clear()
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("Order cancelled.", reply_markup=main_menu_keyboard())
    return ConversationHandler.END


# === ADMIN BOT HANDLERS ===
async def start_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to Kana Foods Admin Dashboard.\nCommands:\n/orders – View all customer orders\n/help – Show this message"
    )


async def view_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not USER_ORDERS:
        await update.message.reply_text("No orders yet.")
        return
    lines = ["📦 Current Orders:"]
    for uid, o in USER_ORDERS.items():
        lines.append(f"- {o['customer']}: {PRODUCTS[o['product_id']]['name']} × {o['qty']} ({o['total']} birr)")
    await update.message.reply_text("\n".join(lines))


# === Build bots ===
def build_customer_bot():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("2"), handle_menu_text)],
        states={
            ASK_PRODUCT: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_product)],
            ASK_QTY: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_qty)],
            CONFIRM_ORDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_order)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True,
    )

    app.add_handler(CommandHandler("start", start_customer))
    app.add_handler(conv_handler)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_menu_text))
    return app


def build_admin_bot():
    app = ApplicationBuilder().token(ADMIN_TOKEN).build()
    app.add_handler(CommandHandler("start", start_admin))
    app.add_handler(CommandHandler("orders", view_orders))
    return app


async def main():
    print("Starting Kana Foods bots...")
    customer_bot = build_customer_bot()
    admin_bot = build_admin_bot()

    # Run both bots concurrently
    async with customer_bot, admin_bot:
        await asyncio.gather(
            customer_bot.start(),
            admin_bot.start(),
            customer_bot.updater.start_polling(),
            admin_bot.updater.start_polling(),
        )


if __name__ == "__main__":
    asyncio.run(main())
