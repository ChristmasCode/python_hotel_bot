import telebot
from telebot import types
# from bot_requests.low_price import low_price


TOKEN = '5511162987:AAGtehigXviygciyEJHdfBRgr8zVwzJtdh4'
bot = telebot.TeleBot(TOKEN)

bot_help = "/lowprice - Search of the cheapest hotels in the city\n" \
           "/highprice - Search of the most expensive hotels in the city\n" \
           "/bestdeal - Search for the most suitable hotels for price and location " \
           "from the city center\n" \
           "/history - hotel search history\n" \
           "/help"


@bot.message_handler(commands=["info"])
def get_start_messages(message):
    bot.send_message(message.from_user.id, "Hello! I can execute the following commands:\n" + str(bot_help))


@bot.message_handler(commands=["start"])
def get_commands_messages(message):
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    key_lowprice = types.InlineKeyboardButton(text="/lowprice", callback_data="lowprice")
    key_highprice = types.InlineKeyboardButton(text="/highprice", callback_data="highprice")
    key_bestdeal = types.InlineKeyboardButton(text="/bestdeal", callback_data="bestdeal")
    key_history = types.InlineKeyboardButton(text="/history", callback_data="history")
    keyboard.add(key_lowprice, key_bestdeal, key_highprice, key_history)
    bot.send_message(message.chat.id, "commands:", reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: True)
def answer(call):
    if call.data == "lowprice":
        bot.send_message(call.message.chat.id, "lowprice")
    if call.data == "highprice":
        bot.send_message(call.message.chat.id, "highprice")
    if call.data == "bestdeal":
        bot.send_message(call.message.chat.id, "bestdeal")
    if call.data == "history":
        bot.send_message(call.message.chat.id, "history")
    bot.answer_callback_query(callback_query_id=call.id)


@bot.message_handler(commands=["help"])
def get_text_messages(message):
    bot.send_message(message.from_user.id, bot_help)


bot.polling(none_stop=True, interval=0)
