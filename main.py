import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    filters, ContextTypes, ConversationHandler
)

# --- ЛОГИ ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- НАСТРОЙКИ ---
TOKEN = '8724604621:AAFiprY9AYmScrOE_8OckFKHMNsRuC4LNeI'  # обязательно смени!
ADMIN_ID = 1028473852


# --- СОСТОЯНИЯ ---
DESCRIPTION, PHOTO, LOCATION = range(3)

# --- КНОПКИ ---
CANCEL = '❌ Отмена'
FEEDBACK_BTN = '💡 Сообщить о проблеме'

# --- КЛАВИАТУРЫ ---
main_keyboard = ReplyKeyboardMarkup([[FEEDBACK_BTN]], resize_keyboard=True)
cancel_keyboard = ReplyKeyboardMarkup([[CANCEL]], resize_keyboard=True)
location_keyboard = ReplyKeyboardMarkup([
    [KeyboardButton("📍 Отправить текущую локацию", request_location=True)],
    [CANCEL]
], resize_keyboard=True)


# --- START ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "💡 Нажмите кнопку ниже, чтобы отправить предложение.",
        reply_markup=main_keyboard
    )


# --- START FEEDBACK ---
async def feedback_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "⚠️ Отправьте сообщение по шаблону:\n\n"
        "👤 ФИО\n"
        "📍 Место\n"
        "📝 Суть проблемы",
        reply_markup=cancel_keyboard
    )
    return DESCRIPTION


# --- ОПИСАНИЕ ---
async def get_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == CANCEL:
        return await cancel(update, context)

    context.user_data['description'] = update.message.text

    await update.message.reply_text(
        """"📷 Шаг 2: Сделайте фотографию проблемы.
Нажмите на иконку 📎 и сделайте фото""",
        reply_markup=cancel_keyboard
    )
    return PHOTO


# --- ФОТО ---
async def get_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == CANCEL:
        return await cancel(update, context)

    if update.message.photo:
        context.user_data['photo'] = update.message.photo[-1].file_id

        await update.message.reply_text(
            """📍 Шаг 3: Отправьте геолокацию.
⚠️ включите геоданные и нажмите на 'отправить текущее местоположение'""",
            reply_markup=location_keyboard
        )
        return LOCATION

    await update.message.reply_text("❗ Нужно отправить фото.")
    return PHOTO


# --- ЛОКАЦИЯ ---
async def get_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == CANCEL:
        return await cancel(update, context)

    if not update.message.location:
        await update.message.reply_text("❗ Нажмите кнопку выше.")
        return LOCATION

    lat = update.message.location.latitude
    lon = update.message.location.longitude

    user = update.message.from_user
    username = f"@{user.username}" if user.username else f"ID: {user.id}"

    # ✅ ИСПРАВЛЕННАЯ ССЫЛКА
    maps_url = f"https://www.google.com/maps?q={lat},{lon}"

    report = (
        f"💡 НОВОЕ ПРЕДЛОЖЕНИЕ\n\n"
        f"👤 От: {username}\n"
        f"📝 Описание: {context.user_data.get('description')}\n\n"
        f"📍 Карта: {maps_url}"
    )

    try:
        await context.bot.send_photo(
            chat_id=ADMIN_ID,
            photo=context.user_data['photo'],
            caption=report
        )

        await update.message.reply_text(
            "✅ Отправлено!",
            reply_markup=main_keyboard
        )

    except Exception as e:
        logger.error(f"Ошибка: {e}")
        await update.message.reply_text("Ошибка отправки.")

    context.user_data.clear()
    return ConversationHandler.END


# --- ОТМЕНА ---
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("❌ Отменено.", reply_markup=main_keyboard)
    return ConversationHandler.END


# --- MAIN ---
def main():
    app = (
        Application.builder()
        .token(TOKEN)
        .build()
    )

    feedback_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex(f'^{FEEDBACK_BTN}$'), feedback_start)],
        states={
            DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_description)],
            PHOTO: [MessageHandler((filters.PHOTO | filters.TEXT) & ~filters.COMMAND, get_photo)],
            LOCATION: [MessageHandler((filters.LOCATION | filters.TEXT) & ~filters.COMMAND, get_location)],
        },
        fallbacks=[MessageHandler(filters.Regex(f'^{CANCEL}$'), cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(feedback_handler)

    print("Бот запущен...")
    app.run_polling()


if __name__ == "__main__":
    main()