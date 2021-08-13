import os
from dotenv import load_dotenv
import telebot

load_dotenv()

SSC_BOT_KEY = os.getenv("SSC_BOT_KEY")
bot = telebot.TeleBot(SSC_BOT_KEY)

@bot.message_handler(commands=['greet'])
def greet(message):
  bot.send_message(message.chat.id, "hey!")

bot.polling()