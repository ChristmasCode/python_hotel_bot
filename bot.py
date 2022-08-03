import telebot
from telebot import types
from bot_requests.low_price import get_city, get_properties, answer_low_hotel_list

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
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    key_lowprice = types.InlineKeyboardButton(text="/lowprice", callback_data="lowprice")
    key_highprice = types.InlineKeyboardButton(text="/highprice", callback_data="highprice")
    key_bestdeal = types.InlineKeyboardButton(text="/bestdeal", callback_data="bestdeal")
    key_history = types.InlineKeyboardButton(text="/history", callback_data="history")
    keyboard.add(key_lowprice, key_bestdeal, key_highprice, key_history)
    bot.send_message(message.chat.id, "commands:", reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: True)
def answer(call):
    if call.data == "lowprice":
        mesg = bot.send_message(call.from_user.id, 'Enter the city where you want to search: ')
        bot.register_next_step_handler(mesg, low_price_city_request)
    elif call.data == "highprice":
        bot.send_message(call.message.chat.id, "highprice")
    elif call.data == "bestdeal":
        bot.send_message(call.message.chat.id, "bestdeal")
    elif call.data == "history":
        bot.send_message(call.message.chat.id, "history")
    # else:
    #     get_properties(int(call.data))
    bot.answer_callback_query(callback_query_id=call.id)


@bot.message_handler(commands=["help"])
def get_text_messages(message):
    bot.send_message(message.from_user.id, bot_help)


@bot.message_handler(commands=["lowprice"])
def low_price_city_request(message):
    cities_districts = get_city(message.text)
    print("BOT LOG: cities_districts ", cities_districts)
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keys = {}
    for city_name, city_id in cities_districts.items():
        # button = types.InlineKeyboardButton(text=city_name, callback_data=city_id)
        # keyboard.add(button)
        keys[city_id] = types.InlineKeyboardButton(text=str(city_name), callback_data=city_id)
        keyboard.add(keys[city_id])
    mesg = bot.send_message(message.chat.id, 'Make your choice:',  reply_markup=keyboard)
    bot.register_next_step_handler(mesg, low_price_city_answer)
    # print(mesg.text)
    # print(keys)in


@bot.callback_query_handler(func=lambda call: True)
def low_price_city_answer(message):
    mesg = message.text
    bot.send_message(message.chat.id, mesg)


bot.polling(none_stop=True, interval=0)
