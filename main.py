import os
from telebot import TeleBot
from keyboa import Keyboa


def hotel_bot():

    TOKEN = '5511162987:AAGtehigXviygciyEJHdfBRgr8zVwzJtdh4'
    bot = TeleBot(token=TOKEN)

    @bot.message_handler(content_types=['text'])
    def get_text_messages(message):
        if message.text == "Привет".lower():
            bot_requests = ["/lowprice", "/highprice", "/bestdeal", "/history", "/help"]
            keyboard = Keyboa(items=bot_requests, copy_text_to_callback=True, items_in_row=3)
            bot.send_message(chat_id=1170996506, text='Hello! Please select one:', reply_markup=keyboard())
        elif message.text == "/help":
            bot.send_message(message.from_user.id, "Я могу выполнить следующие команды:")
            bot.send_message(message.from_user.id, "/lowprice — вывод самых дешёвых отелей в городе")
            bot.send_message(message.from_user.id, "/highprice — вывод самых дорогих отелей в городе")
            bot.send_message(message.from_user.id,
                             "/bestdeal — вывод отелей, наиболее подходящих по цене и расположению "
                             "от центра")
            bot.send_message(message.from_user.id, "/history — вывод истории поиска отелей")
        else:
            bot.send_message(message.from_user.id, "Я тебя не понимаю. Напиши /help.")

    bot.polling(none_stop=True, interval=0)


hotel_bot()
