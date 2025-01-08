# Load Django environment settings
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MySQLandDjango.settings')  # Replace with your project settings module
django.setup()

# Import the transliteration functions
from employees.views import transliterate_ua_text, transliterate_ru_text
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackContext,
    ConversationHandler,
)
from decouple import config
from employees.models import Message
from asgiref.sync import sync_to_async

# Define states
LANGUAGE_SELECTION, TRANSLITERATION = range(2)


# Define a function to handle the 'start' command
async def start(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user

    # Send a welcome message
    await update.message.reply_text(
        f"Hello, {user.first_name}! 👋\n"
        f"I can transliterate your text into Ukrainian or Russian.\n"
        f"Please select a target language:",
        reply_markup=ReplyKeyboardMarkup(
            [[KeyboardButton("Ukrainian 🇺🇦")], [KeyboardButton("Russian 🇺🇦")]],
            one_time_keyboard=True,
            resize_keyboard=True
        )
    )
    return LANGUAGE_SELECTION  # Move to language selection state


# Handle language selection
async def set_language(update: Update, context: CallbackContext) -> int:
    language = update.message.text
    if language == "Ukrainian 🇺🇦":
        context.user_data["language"] = "ua"
    elif language == "Russian 🇺🇦":
        context.user_data["language"] = "ru"
    else:
        await update.message.reply_text("Invalid selection. Please choose Ukrainian or Russian.")
        return LANGUAGE_SELECTION  # Retry language selection

    # Move to transliteration step
    await update.message.reply_text("Great! Send me the text you want to transliterate.")
    return TRANSLITERATION


# Handle transliteration
async def transliterate(update: Update, context: CallbackContext) -> int:
    text = update.message.text
    language = context.user_data.get("language")
    chat_id = update.message.chat_id  # Get Telegram chat ID

    # Transliterate text based on selected language
    if language == "ua":
        converted_text = transliterate_ua_text(text)
    elif language == "ru":
        converted_text = transliterate_ru_text(text)
    else:
        await update.message.reply_text("Something went wrong. Please restart.")
        return ConversationHandler.END

    await update.message.reply_text(f"Here's your transliterated text:")
    await update.message.reply_text(f"{converted_text}")

    # Save message to database asynchronously
    try:
        await sync_to_async(Message.objects.create)(
            id_chat=chat_id,
            platform="telegram",
            lang=language,
            message=converted_text
        )
        print("Message successfully saved to the database.")
    except Exception as e:
        print(f"Error saving message: {e}")

    return TRANSLITERATION  # Allow sending more messages


# Handle fallback (display the "Start" message)
async def fallback(update: Update, context: CallbackContext) -> int:
    """Fallback handler for any unrecognized input."""
    # If the bot restarts, show the start message as a fallback
    return await start(update, context)


# Cancel or end interaction
async def cancel(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text("Goodbye! 👋")
    return ConversationHandler.END


# Main bot function
def correct_keyboard_bot(token: str):
    application = Application.builder().token(token).build()

    # Define ConversationHandler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            LANGUAGE_SELECTION: [MessageHandler(filters.TEXT, set_language)],
            TRANSLITERATION: [MessageHandler(filters.TEXT, transliterate)],
        },
        fallbacks=[MessageHandler(filters.ALL, fallback)],  # Catch all inputs and redirect to start
    )

    # Add the conversation handler to the Application
    application.add_handler(conv_handler)

    # Start the bot
    print("Bot is running! Press Ctrl+C to stop.")
    application.run_polling()


if __name__ == "__main__":
    # Replace with your bot token
    BOT_TOKEN = config('BOT_TOKEN')  # Get the bot token from the .env file
    correct_keyboard_bot(BOT_TOKEN)
