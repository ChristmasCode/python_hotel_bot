import requests
import json
from api_key import api_key


def get_hotel_photo(hotel_id, photo_count):
    url = "https://hotels4.p.rapidapi.com/properties/get-hotel-photos"

    querystring = {"id": hotel_id}
    answer = []

    headers = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": "hotels4.p.rapidapi.com"
    }

    photos = []
    response = requests.request("GET", url, headers=headers, params=querystring, timeout=60)

    if response:
        data = json.loads(response.text)
        for photo in data["hotelImages"]:
            url = photo.get("baseUrl").replace("_{size}", "")
            photos.append(url)

    for photo in range(min(int(photo_count), len(photos))):
        answer.append(photos[photo])
    if min(int(photo_count), len(photos)) == len(photos):
        answer.append("Sorry, just found photos: " + str(len(photos)))

    return answer

