import telebot
from telebot import types
from telegram_bot_calendar import DetailedTelegramCalendar, LSTEP
from bot_requests.low_price import get_city, lowprice_get_properties
from loguru import logger


TOKEN = '5511162987:AAGtehigXviygciyEJHdfBRgr8zVwzJtdh4'
bot = telebot.TeleBot(TOKEN)

bot_help = "/lowprice - Search of the cheapest hotels in the city\n" \
           "/highprice - Search of the most expensive hotels in the city\n" \
           "/bestdeal - Search for the most suitable hotels for price and location " \
           "from the city center\n" \
           "/history - hotel search history\n" \
           "/help"

db_dict = {}


@bot.message_handler(commands=["info"])
@logger.catch()
def get_start_messages(message):
    bot.send_message(message.from_user.id, "Hello! I can execute the following commands:\n" + str(bot_help))


@bot.message_handler(commands=["start"])
@logger.catch()
def get_commands_messages(message):
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    key_lowprice = types.InlineKeyboardButton(text="/lowprice", callback_data="lowprice")
    key_highprice = types.InlineKeyboardButton(text="/highprice", callback_data="highprice")
    key_bestdeal = types.InlineKeyboardButton(text="/bestdeal", callback_data="bestdeal")
    key_history = types.InlineKeyboardButton(text="/history", callback_data="history")
    keyboard.add(key_lowprice, key_bestdeal, key_highprice, key_history)
    bot.send_message(message.chat.id, "commands:", reply_markup=keyboard)


# @bot.message_handler(commands=['calendar'])
@logger.catch()
def bot_calendar(message):
    calendar, step = DetailedTelegramCalendar().build()
    bot.send_message(message.chat.id,
                     f"Select {LSTEP[step]}",
                     reply_markup=calendar)


@bot.callback_query_handler(func=DetailedTelegramCalendar.func())
@logger.catch()
def cal(call):
    result, key, step = DetailedTelegramCalendar().process(call.data)
    if not result and key:
        bot.edit_message_text(f"Select {LSTEP[step]}",
                              call.message.chat.id,
                              call.message.message_id,
                              reply_markup=key)
    elif result:
        bot.edit_message_text(f"You selected {result}",
                              call.message.chat.id,
                              call.message.message_id)
        logger.info(result)
        route_by_state(result, call.from_user.id, call.message.chat.id)


def route_by_state(date, user_id, chat_id):
    state = db_dict[user_id]["state"]
    match state:
        case "date_from":
            db_dict[user_id]["checkIn"] = date
            db_dict[user_id]["state"] = "date_to"
            calendar, step = DetailedTelegramCalendar().build()
            bot.send_message(chat_id, "Select check out date: ")
            bot.send_message(chat_id,
                             f"Select {LSTEP[step]}",
                             reply_markup=calendar)
        case "date_to":
            user = db_dict[user_id]
            db_dict[user_id]["checkOut"] = date
            mesg = bot.send_message(chat_id, "You want to see photos of hotels? ('yes'/'no'): ")
            bot.register_next_step_handler(mesg, bot_photos_request, user_id)
            # lowprice_get_properties(
            #     city_id=user["city"],
            #     number_of_hotels=user["number_of_hotels"],
            #     data_in=user["checkIn"],
            #     data_out=user["checkOut"]
            # )


def bot_photos_request(message, user_id):
    mesg = message.text.lower()
    logger.info(mesg)
    match mesg:
        case "yes":
            how_many_photos = bot.send_message(message.chat.id, "How many photos? (no more than 10) ")
            bot.register_next_step_handler(how_many_photos, bot_photos_count, message.from_user.id)
        case "no":
            pass
            # user = db_dict[user_id]
            # lowprice_get_properties(
            #     city_id=user["city"],
            #     number_of_hotels=user["number_of_hotels"],
            #     data_in=user["checkIn"],
            #     data_out=user["checkOut"],
            #     photos_count=0
            # )
        case _:
            mesg = bot.send_message(message.chat.id, "You want to see photos of hotels? ('yes'/'no'): ")
            bot.register_next_step_handler(mesg, bot_photos_request)


def bot_photos_count(message, user_id):
    mesg = message.text.lower()
    logger.info(mesg)
    if not (mesg.isnumeric() and int(mesg) > 0):
        bot.send_message(message.chat.id, "Enter an integer, a positive number")
        how_many_photos = bot.send_message(message.chat.id, "How many photos? (no more than 10) ")
        bot.register_next_step_handler(how_many_photos, bot_photos_count)
    if mesg.isnumeric() and int(mesg) > 0:
        user = db_dict[user_id]
        db_dict[user_id]["photos_count"] = mesg
        logger.info(db_dict)
        final_answer = lowprice_get_properties(
            city_id=user["city"],
            number_of_hotels=user["number_of_hotels"],
            data_in=user["checkIn"],
            data_out=user["checkOut"],
            photos_count=user["photos_count"]
        )

        bot.send_message(message.chat.id, "Search is over: ")
        logger.info(final_answer)
        for hotel in final_answer:
            for key, value in hotel.items():
                if key == "Photo":
                    if value[-1].startswith("Sorry, just found photos"):
                        if value[-1] == 'Sorry, just found photos: 0':
                            bot.send_message(message.chat.id, "Sorry hotel photos not found")
                        else:
                            bot.send_media_group(message.chat.id, value[-1])
                            bot.send_media_group(message.chat.id,
                                                 [telebot.types.InputMediaPhoto(photo) for photo in value])
                    else:
                        bot.send_media_group(message.chat.id,
                                             [telebot.types.InputMediaPhoto(photo) for photo in value])
                else:
                    bot.send_message(message.chat.id, key + " : " + value)

        # bot.register_next_step_handler(final_answer, low_final_answer)


# def low_final_answer(message, final_answer):
#     mesg = final_answer
#     logger.info(mesg)
    # for value in mesg:
    #     bot.send_message(message.chat.id, value)


    # match mesg:
    #     case int():
    #         bot.send_message(message.chat.id, mesg)
    #     case _:
    #         bot.send_message(message.chat.id, "Enter an integer, a positive number")
    #         how_many_photos = bot.send_message(message.chat.id, "How many photos? (no more than 10) ")
    #         bot.register_next_step_handler(how_many_photos, bot_photos_count)


@bot.callback_query_handler(func=lambda call: True)
@logger.catch()
def answer(call):
    logger.info(call)
    match call.data:
        case "lowprice":
            mesg = bot.send_message(call.from_user.id, "Enter the city where you want to search: ")
            bot.register_next_step_handler(mesg, low_price_city_request)
        case "highprice":
            bot.send_message(call.message.chat.id, "highprice")
        case "bestdeal":
            bot.send_message(call.message.chat.id, "bestdeal")
        case "history":
            bot.send_message(call.message.chat.id, "history")
        case _:
            if call.data.startswith("lowprice_answer"):
                mesg_city_id = call.message.chat.id, call.data.replace("lowprice_answer", '')
                db_dict[call.from_user.id] = {"city": mesg_city_id[1]}
                logger.info(db_dict)
                logger.info(mesg_city_id)
                mesg = bot.send_message(call.from_user.id, "How many hotels to show: ")
                bot.register_next_step_handler(mesg, count_hotels)


@bot.message_handler(commands=["help"])
@logger.catch()
def get_text_messages(message):
    bot.send_message(message.from_user.id, bot_help)


@bot.message_handler(commands=["lowprice"])
@logger.catch()
def low_price_city_request(message):
    cities_districts = get_city(message.text)
    logger.info(cities_districts)
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    for city_name, city_id in cities_districts.items():
        button = types.InlineKeyboardButton(
            text=city_name,
            callback_data="lowprice_answer" + city_id
        )
        keyboard.add(button)
    mesg = bot.send_message(message.chat.id, 'Make your choice:', reply_markup=keyboard)
    bot.register_next_step_handler(mesg, low_price_city_answer)


@bot.message_handler(chat_types="text")
def count_hotels(message):
    mesg = message.text
    db_dict[message.from_user.id]["number_of_hotels"] = mesg
    db_dict[message.from_user.id]["state"] = "date_from"
    logger.info(mesg)
    logger.info(db_dict)
    calendar, step = DetailedTelegramCalendar().build()
    bot.send_message(message.chat.id, "Select check in date: ")
    bot.send_message(message.chat.id,
                     f"Select {LSTEP[step]}",
                     reply_markup=calendar)


def low_price_city_answer(message):
    mesg = message.text
    logger.info(mesg)
    return mesg


bot.polling(none_stop=True, interval=0)
