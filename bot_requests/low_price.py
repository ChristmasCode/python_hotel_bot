import json
import requests


def low_price():

    """
    Функция lowprice.
        Запрашивает:
            - Город, где будет проводиться поиск.

            - Количество отелей, которые необходимо вывести в результате (не больше
            заранее определённого максимума).

            - Необходимость загрузки и вывода фотографий для каждого отеля («Да/Нет»):
                - При положительном ответе пользователь также вводит количество
                необходимых фотографий (не больше заранее определённого
                максимума).
    """

    def get_location():

        url = "https://hotels4.p.rapidapi.com/locations/v2/search"

        querystring = {
            "query": input('Введите город, где будет проводиться поиск: '),
            "locale": "en_US",
            "currency": "USD"
        }

        headers = {
            "X-RapidAPI-Key": "308a0ecd4dmsh778f749df86bb27p1e009ajsn881d6b34ec98",
            "X-RapidAPI-Host": "hotels4.p.rapidapi.com"
        }

        response = requests.request("GET", url, headers=headers, params=querystring)
        result = json.loads(response.text)

        # with open('location_answer', 'w+') as file:
        #     json.dump(result, file, indent=4)

        return result

    def get_city():
        result_location = get_location()
        list_suggestions = result_location.get('suggestions')
        group_city = list_suggestions[0]
        list_city_name = [name.get('name') for name in group_city.get('entities')]
        list_destinationId = [destinationId.get('destinationId') for destinationId in group_city.get('entities')]
        print(list_city_name)
        print(list_destinationId)

    def get_properties():
        url = "https://hotels4.p.rapidapi.com/properties/list"

        querystring = {"destinationId": "1506246", "pageNumber": "1", "pageSize": "25", "checkIn": "2020-01-08",
                       "checkOut": "2020-01-15", "adults1": "1", "sortOrder": "PRICE", "locale": "en_US",
                       "currency": "USD"}

        headers = {
            "X-RapidAPI-Key": "308a0ecd4dmsh778f749df86bb27p1e009ajsn881d6b34ec98",
            "X-RapidAPI-Host": "hotels4.p.rapidapi.com"
        }

        response = requests.request("GET", url, headers=headers, params=querystring)

    get_city()


low_price()
