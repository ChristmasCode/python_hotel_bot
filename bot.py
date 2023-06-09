import json
import datetime
import os

import peewee
from dotenv import load_dotenv

import telebot
from loguru import logger
from telebot import types
from telegram_bot_calendar import LSTEP, DetailedTelegramCalendar

from bot_requests.best_deal import best_get_city, best_get_properties
from bot_requests.high_price import high_get_city, high_get_properties
from bot_requests.history import read, read_time, read_command, record
from bot_requests.low_price import low_get_city, lowprice_get_properties
from models import *

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
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
    calendar, step = DetailedTelegramCalendar(min_date=datetime.datetime.now().date()).build()
    bot.send_message(message.chat.id,
                     f"Select {LSTEP[step]}",
                     reply_markup=calendar)


@bot.callback_query_handler(func=DetailedTelegramCalendar.func())
@logger.catch()
def cal(call):
    result, key, step = DetailedTelegramCalendar(min_date=datetime.datetime.now().date()).process(call.data)
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
            calendar, step = DetailedTelegramCalendar(min_date=datetime.datetime.now().date()).build()
            bot.send_message(chat_id, "Select check out date: ")
            bot.send_message(chat_id,
                             f"Select {LSTEP[step]}",
                             reply_markup=calendar)
        case "date_to":
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
    calendar, step = DetailedTelegramCalendar(min_date=datetime.datetime.now().date()).build()
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
                current_time = datetime.datetime.now()
                logger.info(current_time)
                current_command = "/lowprice"
                record(final_answer, user_id, current_time, current_command)

            elif db_dict[user_id]["price"] == "high":
                final_answer = high_get_properties(
                    city_id=user["city"],
                    number_of_hotels=user["number_of_hotels"],
                    data_in=user["checkIn"],
                    data_out=user["checkOut"],
                    photos_count=0
                )
                current_time = datetime.datetime.now()
                logger.info(current_time)
                current_command = "/highprice"
                record(final_answer, user_id, current_time, current_command)

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
                current_time = datetime.datetime.now()
                logger.info(current_time)
                current_command = "/bestdeal"
                record(final_answer, user_id, current_time, current_command)
            bot.send_message(message.chat.id, "Search is over: ")

            for hotel in final_answer:
                bot.send_message(message.chat.id, "Next hotel ⬇")
                answer_message = ""
                for key, value in hotel.items():
                    answer_message += key + " : " + value + "\n"
                    if key == "📷 Photo":
                        pass
                else:
                    bot.send_message(message.chat.id, answer_message,
                                     disable_web_page_preview=True)

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
            current_time = datetime.datetime.now()
            logger.info(current_time)
            current_command = "/lowprice"
            record(final_answer, user_id, current_time, current_command)

        elif db_dict[user_id]["price"] == "high":
            final_answer = high_get_properties(
                city_id=user["city"],
                number_of_hotels=user["number_of_hotels"],
                data_in=user["checkIn"],
                data_out=user["checkOut"],
                photos_count=user["photos_count"]
            )
            current_time = datetime.datetime.now()
            logger.info(current_time)
            current_command = "/highprice"
            record(final_answer, user_id, current_time, current_command)

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
            current_time = datetime.datetime.now()
            logger.info(current_time)
            current_command = "/beastdeal"
            record(final_answer, user_id, current_time, current_command)

        bot.send_message(message.chat.id, "Search is over: ")
        logger.info(final_answer)

        for hotel in final_answer:
            logger.info(hotel)
            bot.send_message(message.chat.id, "Next hotel ⬇")
            answer_message = ""
            for key, value in hotel.items():
                if key != "📷 Photo":
                    answer_message += str(key) + " : " + str(value) + "\n"
                if key == "📷 Photo":
                    if value[-1].startswith("Sorry, just found photos"):
                        if value[-1] == 'Sorry, just found photos: 0':
                            bot.send_message(message.from_user.id, "Sorry hotel photos not found")
                        else:
                            bot.send_message(message.from_user.id, value[-1])
                            bot.send_media_group(message.from_user.id,
                                                 [telebot.types.InputMediaPhoto(photo) for photo in value])
                    else:
                        bot.send_media_group(message.from_user.id,
                                             [telebot.types.InputMediaPhoto(photo) for photo in value])
            else:
                bot.send_message(message.from_user.id, answer_message,
                                 disable_web_page_preview=True)


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
            logger.info(call.from_user.id)
            mesg = bot.send_message(call.from_user.id, "Enter the city where you want to search: ")
            bot.register_next_step_handler(mesg, low_price_city_request)
        case "highprice":
            logger.info(call.from_user.id)
            mesg = bot.send_message(call.from_user.id, "Enter the city where you want to search: ")
            bot.register_next_step_handler(mesg, hight_price_city_request)
        case "bestdeal":
            logger.info(call.from_user.id)
            mesg = bot.send_message(call.from_user.id, "Enter the city where you want to search: ")
            bot.register_next_step_handler(mesg, best_price_city_request)
        case "history":
            logger.info(call.from_user.id)
            history = read(call.from_user.id)
            history_command = read_command(call.from_user.id)
            history_time = read_time(call.from_user.id)
            history_iterator = 0

            query = User.select(User.telegram_id).where(User.telegram_id == call.from_user.id)
            if query.exists():
                for request in history:
                    req_command = history_command[history_iterator].get("input_command")
                    req_time = str(history_time[history_iterator].get("current_time"))
                    bot.send_message(call.from_user.id, "📣 Your request: " + req_command +
                                     "\n" +
                                     "📅 Time of request: " + req_time[:-7])
                    history_iterator += 1
                    logger.info(request)
                    temp = request.get("request")
                    temp = str(temp).replace('\'', '"')
                    temp = str(temp).replace('💩', "'")
                    temp = json.loads(temp)
                    for req in temp:
                        bot.send_message(call.from_user.id, "Next hotel ⬇")
                        answer_message = ""
                        for key, value in req.items():
                            if key != "📷 Photo":
                                answer_message += str(key) + " : " + str(value) + "\n"
                            else:
                                if isinstance(value, str):
                                    if value.startswith("Sorry, just found photos"):
                                        if value == 'Sorry, just found photos: 0':
                                            bot.send_message(call.from_user.id, "Sorry hotel photos not found")
                                else:
                                    bot.send_media_group(call.from_user.id,
                                                         [telebot.types.InputMediaPhoto(photo) for photo in value])
                        else:
                            bot.send_message(call.from_user.id, answer_message,
                                             disable_web_page_preview=True)
            else:
                bot.send_message(call.from_user.id, "Your search history is empty")

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


def low_price_city_answer(message) -> str:
    mesg = message.text
    logger.info(mesg)
    return mesg


def high_price_city_answer(message) -> str:
    mesg = message.text
    logger.info(mesg)
    return mesg


def best_price_city_answer(message) -> str:
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
