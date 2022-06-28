import requests
from python_basic_diploma import hotel_bot


def get_data(url):
    querystring = {"query": "new york", "locale": "en_US", "currency": "USD"}
    headers = {
        "X-RapidAPI-Key": "308a0ecd4dmsh778f749df86bb27p1e009ajsn881d6b34ec98",
        "X-RapidAPI-Host": "hotels4.p.rapidapi.com"
    }
    response = requests.request("GET", url, headers=headers, params=querystring)
    print(response.text)


def main():
    get_data("https://hotels4.p.rapidapi.com/locations/v2/search", )

    hotel_bot


if __name__ == '__main__':
    main()
