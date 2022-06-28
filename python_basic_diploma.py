import telebot

TOKEN = '5511162987:AAGtehigXviygciyEJHdfBRgr8zVwzJtdh4'

hotel_bot = telebot.TeleBot(TOKEN)


@hotel_bot.message_handler(content_types=['text'])
def get_text_messages(message):
    if message.text == "Привет".lower():
        hotel_bot.send_message(message.from_user.id, "Привет, чем я могу тебе помочь?")
    elif message.text == "/help":
        hotel_bot.send_message(message.from_user.id, "Я могу выполнить следующие команды:")
        hotel_bot.send_message(message.from_user.id, "/lowprice — вывод самых дешёвых отелей в городе")
        hotel_bot.send_message(message.from_user.id, "/highprice — вывод самых дорогих отелей в городе")
        hotel_bot.send_message(message.from_user.id,
                               "/bestdeal — вывод отелей, наиболее подходящих по цене и расположению "
                               "от центра")
        hotel_bot.send_message(message.from_user.id, "/history — вывод истории поиска отелей")
    else:
        hotel_bot.send_message(message.from_user.id, "Я тебя не понимаю. Напиши /help.")


hotel_bot.polling(none_stop=True, interval=0)
