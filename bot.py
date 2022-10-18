import json
import telebot
from telebot import types
from telegram_bot_calendar import DetailedTelegramCalendar, LSTEP
from bot_requests.low_price import low_get_city, lowprice_get_properties
from bot_requests.high_price import high_get_city, high_get_properties
from bot_requests.best_deal import best_get_city, best_get_properties
from loguru import logger
from models import *
from bot_requests.history import record
from bot_requests.history import read

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
    if not User.select().where(User.telegram_id == message.chat.id):
        User.create(telegram_id=message.chat.id)


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


def bot_photos_request(message, user_id):
    mesg = message.text.lower()
    logger.info(mesg)
    match mesg:
        case "yes":
            how_many_photos = bot.send_message(message.chat.id, "How many photos?")
            bot.register_next_step_handler(how_many_photos, bot_photos_count, message.from_user.id)
        case "no":
            user = db_dict[user_id]
            final_answer = None
            if db_dict[user_id]["price"] == "low":
                final_answer = lowprice_get_properties(
                    city_id=user["city"],
                    number_of_hotels=user["number_of_hotels"],
                    data_in=user["checkIn"],
                    data_out=user["checkOut"],
                    photos_count=0
                )

            elif db_dict[user_id]["price"] == "high":
                final_answer = high_get_properties(
                    city_id=user["city"],
                    number_of_hotels=user["number_of_hotels"],
                    data_in=user["checkIn"],
                    data_out=user["checkOut"],
                    photos_count=0
                )
            elif db_dict[user_id]["price"] == "best":
                final_answer = best_get_properties(
                    city_id=user["city"],
                    number_of_hotels=user["number_of_hotels"],
                    data_in=user["checkIn"],
                    data_out=user["checkOut"],
                    price_range_min=user["price_range_min"],
                    price_range_max=user["price_range_max"],
                    photos_count=0,
                    city_center_min=user["city_center_min"],
                    city_center_max=user["city_center_max"]
                )
            bot.send_message(message.chat.id, "Search is over: ")
            record(user_id, final_answer)
            for hotel in final_answer:
                bot.send_message(message.chat.id, "Next hotel ⬇")
                for key, value in hotel.items():
                    if key == "📷 Photo":
                        pass
                    else:
                        bot.send_message(message.chat.id, key + " : " + value)

        case _:
            mesg = bot.send_message(message.chat.id, "You want to see photos of hotels? ('yes'/'no'): ")
            bot.register_next_step_handler(mesg, bot_photos_request)


def bot_photos_count(message, user_id):
    mesg = message.text.lower()
    logger.info(mesg)
    if not (mesg.isnumeric() and int(mesg) > 0):
        bot.send_message(message.chat.id, "Enter an integer, a positive number")
        how_many_photos = bot.send_message(message.chat.id, "How many photos?")
        bot.register_next_step_handler(how_many_photos, bot_photos_count)
    if mesg.isnumeric() and int(mesg) > 0:
        user = db_dict[user_id]
        db_dict[user_id]["photos_count"] = mesg
        logger.info(db_dict)
        final_answer = None
        if db_dict[user_id]["price"] == "low":
            final_answer = lowprice_get_properties(
                city_id=user["city"],
                number_of_hotels=user["number_of_hotels"],
                data_in=user["checkIn"],
                data_out=user["checkOut"],
                photos_count=user["photos_count"]
            )
        elif db_dict[user_id]["price"] == "high":
            final_answer = high_get_properties(
                city_id=user["city"],
                number_of_hotels=user["number_of_hotels"],
                data_in=user["checkIn"],
                data_out=user["checkOut"],
                photos_count=user["photos_count"]
            )
        elif db_dict[user_id]["price"] == "best":
            final_answer = best_get_properties(
                city_id=user["city"],
                number_of_hotels=user["number_of_hotels"],
                data_in=user["checkIn"],
                data_out=user["checkOut"],
                price_range_min=user["price_range_min"],
                price_range_max=user["price_range_max"],
                photos_count=user["photos_count"],
                city_center_min=user["city_center_min"],
                city_center_max=user["city_center_max"]
            )
        bot.send_message(message.chat.id, "Search is over: ")
        logger.info(final_answer)
        record(user_id, final_answer)
        for hotel in final_answer:
            logger.info(hotel)
            bot.send_message(message.chat.id, "Next hotel ⬇")
            for key, value in hotel.items():
                if key == "📷 Photo":
                    if value[-1].startswith("Sorry, just found photos"):
                        if value[-1] == 'Sorry, just found photos: 0':
                            bot.send_message(message.chat.id, "Sorry hotel photos not found")
                        else:
                            bot.send_message(message.chat.id, value[-1])
                            bot.send_media_group(message.chat.id,
                                                 [telebot.types.InputMediaPhoto(photo) for photo in value])
                    else:
                        bot.send_media_group(message.chat.id,
                                             [telebot.types.InputMediaPhoto(photo) for photo in value])
                else:
                    bot.send_message(message.chat.id, key + " : " + value)


@bot.message_handler(commands=["help"])
@logger.catch()
def get_text_messages(message):
    bot.send_message(message.from_user.id, bot_help)


@bot.message_handler(commands=["lowprice"])
@logger.catch()
def low_price_city_request(message):
    cities_districts = low_get_city(message.text)
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


@bot.message_handler(commands=["highprice"])
@logger.catch()
def hight_price_city_request(message):
    cities_districts = high_get_city(message.text)
    logger.info(cities_districts)
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    for city_name, city_id in cities_districts.items():
        button = types.InlineKeyboardButton(
            text=city_name,
            callback_data="highprice_answer" + city_id
        )
        keyboard.add(button)
    mesg = bot.send_message(message.chat.id, 'Make your choice:', reply_markup=keyboard)
    bot.register_next_step_handler(mesg, high_price_city_answer)


@bot.message_handler(commands=["bestdeal"])
@logger.catch()
def best_price_city_request(message):
    cities_districts = best_get_city(message.text)
    logger.info(cities_districts)
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    for city_name, city_id in cities_districts.items():
        button = types.InlineKeyboardButton(
            text=city_name,
            callback_data="bestdeal_answer" + city_id
        )
        keyboard.add(button)
    mesg = bot.send_message(message.chat.id, 'Make your choice:', reply_markup=keyboard)
    bot.register_next_step_handler(mesg, best_price_city_answer)


@bot.callback_query_handler(func=lambda call: True)
@logger.catch()
def answer(call):
    match call.data:
        case "lowprice":
            mesg = bot.send_message(call.from_user.id, "Enter the city where you want to search: ")
            bot.register_next_step_handler(mesg, low_price_city_request)
        case "highprice":
            mesg = bot.send_message(call.from_user.id, "Enter the city where you want to search: ")
            bot.register_next_step_handler(mesg, hight_price_city_request)
        case "bestdeal":
            mesg = bot.send_message(call.from_user.id, "Enter the city where you want to search: ")
            bot.register_next_step_handler(mesg, best_price_city_request)
        case "history":
            # print(read(1170996506))
            history = read(call.from_user.id)
            for request in history:
                temp = request.get("request")

                temp = str(temp).replace('\'', '"')
                temp = str(temp).replace('💩', "'")


                temp = json.loads(temp)
                # logger.info(temp)
                # logger.info(type(temp))
                for req in temp:
                    for key, value in req.items():
                        if key == "📷 Photo":
                            if value[-1].startswith("Sorry, just found photos"):
                                if value[-1] == 'Sorry, just found photos: 0':
                                    bot.send_message(call.from_user.id, "Sorry hotel photos not found")
                                else:
                                    bot.send_message(call.from_user.id, value[-1])
                                    bot.send_media_group(call.from_user.id,
                                                         [telebot.types.InputMediaPhoto(photo) for photo in value])
                            else:
                                bot.send_media_group(call.from_user.id,
                                                     [telebot.types.InputMediaPhoto(photo) for photo in value])
                        else:
                            bot.send_message(call.from_user.id, str(key) + " : " + str(value))
        case _:
            if call.data.startswith("lowprice_answer"):
                mesg_city_id = call.message.chat.id, call.data.replace("lowprice_answer", '')
                db_dict[call.from_user.id] = {"city": mesg_city_id[1]}
                db_dict[call.from_user.id]["price"] = "low"
                logger.info(db_dict)
                logger.info(mesg_city_id)
                mesg = bot.send_message(call.from_user.id, "How many hotels to show: ")
                bot.register_next_step_handler(mesg, count_hotels)
            elif call.data.startswith("highprice_answer"):
                mesg_city_id = call.message.chat.id, call.data.replace("highprice_answer", '')
                db_dict[call.from_user.id] = {"city": mesg_city_id[1]}
                db_dict[call.from_user.id]["price"] = "high"
                logger.info(db_dict)
                logger.info(mesg_city_id)
                mesg = bot.send_message(call.from_user.id, "How many hotels to show: ")
                bot.register_next_step_handler(mesg, count_hotels)
            elif call.data.startswith("bestdeal_answer"):
                mesg_city_id = call.message.chat.id, call.data.replace("bestdeal_answer", '')
                db_dict[call.from_user.id] = {"city": mesg_city_id[1]}
                db_dict[call.from_user.id]["price"] = "best"
                logger.info(db_dict)
                logger.info(mesg_city_id)
                select = bot.send_message(call.from_user.id, "Select the minimum cost:")
                bot.register_next_step_handler(select, price_min)


def low_price_city_answer(message):
    mesg = message.text
    logger.info(mesg)
    return mesg


def high_price_city_answer(message):
    mesg = message.text
    logger.info(mesg)
    return mesg


def best_price_city_answer(message):
    mesg = message.text
    logger.info(mesg)
    return mesg


def price_min(message):
    mesg = message.text
    logger.info(mesg)
    if not (mesg.isnumeric() and int(mesg) >= 0):
        bot.send_message(message.chat.id, "Enter an integer, a positive number")
        select = bot.send_message(message.from_user.id, "Select the minimum cost:")
        bot.register_next_step_handler(select, price_min)
    if mesg.isnumeric() and int(mesg) >= 0:
        db_dict[message.from_user.id]["price_range_min"] = mesg
        logger.info(db_dict)
        select = bot.send_message(message.from_user.id, "Select the maximum cost:")
        bot.register_next_step_handler(select, price_max)


def price_max(message):
    mesg = message.text
    logger.info(mesg)
    if not (mesg.isnumeric() and int(mesg) and int(mesg) > int(db_dict[message.from_user.id]["price_range_min"])):
        bot.send_message(message.chat.id, "Enter an integer, a positive number, and less than minimum cost")
        select = bot.send_message(message.from_user.id, "Select the maximum cost:")
        bot.register_next_step_handler(select, price_max)
    if mesg.isnumeric() and int(mesg) >= 0:
        db_dict[message.from_user.id]["price_range_max"] = mesg
        logger.info(db_dict)
        mesg = bot.send_message(message.from_user.id, "Choose the minimum distance to the city center:")
        bot.register_next_step_handler(mesg, city_center_min)


def city_center_min(message):
    mesg = message.text
    logger.info(mesg)
    if not (mesg.isnumeric() and int(mesg) >= 0):
        bot.send_message(message.chat.id, "Enter an integer, a positive number")
        select = bot.send_message(message.from_user.id, "Select the minimum cost:")
        bot.register_next_step_handler(select, city_center_min)
    if mesg.isnumeric() and int(mesg) >= 0:
        db_dict[message.from_user.id]["city_center_min"] = mesg
        logger.info(db_dict)
        mesg = bot.send_message(message.from_user.id, "Choose the maximum distance to the city center:")
        bot.register_next_step_handler(mesg, city_center_max)


def city_center_max(message):
    mesg = message.text
    logger.info(mesg)
    if not (mesg.isnumeric() and int(mesg) and int(mesg) > int(db_dict[message.from_user.id]["city_center_min"])):
        bot.send_message(message.chat.id, "Enter an integer, a positive number, and less than minimum range")
        select = bot.send_message(message.from_user.id, "Choose the maximum distance to the city center:")
        bot.register_next_step_handler(select, city_center_max)
    if mesg.isnumeric() and int(mesg) >= 0:
        db_dict[message.from_user.id]["city_center_max"] = mesg
        logger.info(db_dict)
        mesg = bot.send_message(message.from_user.id, "How many hotels to show: ")
        bot.register_next_step_handler(mesg, count_hotels)


bot.polling(none_stop=True, interval=0)

if __name__ == '__main__':
    get_start_messages()
