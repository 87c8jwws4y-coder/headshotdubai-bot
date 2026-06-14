import os
from telebot import TeleBot

TOKEN = os.getenv("BOT_TOKEN")

bot = TeleBot(TOKEN)

@bot.message_handler(commands=["start"])
def start(message):
    bot.reply_to(message, "HeadShotDubai Bot запущен ✅")

bot.infinity_polling()