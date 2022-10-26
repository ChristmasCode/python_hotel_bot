import json
import os
from typing import Any

import requests
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("RAPIDAPI_KEY")


def get_hotel_photo(hotel_id: int, photo_count: int) -> list:
    url = "https://hotels4.p.rapidapi.com/properties/get-hotel-photos"

    querystring: dict[str, int] = {"id": hotel_id}
    answer: list[str | Any] = []

    headers = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": "hotels4.p.rapidapi.com"
    }

    photos: list[Any] = []
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
