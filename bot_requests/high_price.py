import json
import os
from typing import Any

import requests
from dotenv import load_dotenv
from loguru import logger

from bot_requests.photos_request import get_hotel_photo

load_dotenv()

api_key = os.getenv("RAPIDAPI_KEY")


def get_location(city: str) -> dict:
    logger.info(city)
    url = "https://hotels4.p.rapidapi.com/locations/v2/search"

    querystring = {
        "query": str(city),
        "locale": "en_US",
        "currency": "USD"
    }

    headers = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": "hotels4.p.rapidapi.com"
    }

    response = requests.request("GET", url, headers=headers, params=querystring, timeout=60)
    result = json.loads(response.text)

    logger.info(result)
    return result


def high_get_city(city: str) -> dict:
    logger.info(city)
    result_location = get_location(city)
    data_suggestions = result_location.get('suggestions')
    group_city_data = data_suggestions[0]
    logger.info(group_city_data)
    data_city_name = [name.get('name') for name in group_city_data.get('entities')]  # returns a list of cities
    # (city districts)
    logger.info(data_city_name)
    data_destinationId = [destinationId.get('destinationId') for destinationId in group_city_data.get('entities')]  #
    # returns the ID of cities(city districts)
    data_city_id = data_destinationId
    logger.info(data_city_id)
    result = dict(zip(data_city_name, data_city_id))
    logger.info(result)

    return result


def high_get_properties(city_id: int,
                        number_of_hotels: int,
                        data_in: str,
                        data_out: str,
                        photos_count: int) -> list[dict[str, str | int]]:
    url = "https://hotels4.p.rapidapi.com/properties/list"

    photos_count_answer = photos_count

    querystring: dict[str, str | int] = {
        "destinationId": city_id,
        "pageNumber": "1",
        "pageSize": number_of_hotels,
        "checkIn": data_in,
        "checkOut": data_out,
        "adults1": "1",
        "sortOrder": "PRICE_HIGHEST_FIRST",
        "locale": "en_US",
        "currency": "USD"
    }

    headers = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": "hotels4.p.rapidapi.com"
    }

    response = requests.request("GET", url, headers=headers, params=querystring)
    result = json.loads(response.text)

    logger.info(result)
    return get_hotels(result, photos_count_answer)


def get_hotels(result_hotels: dict,
               photos_count_answer: int) -> Any:
    result = (result_hotels['data']['body']['searchResults']['results'])
    logger.info(result)
    return answer_high_hotel_list(result, photos_count_answer)


def answer_high_hotel_list(hotel_answer: dict,
                           photos_count_answer: int) -> list[dict[str, str | list]]:
    photo_count = photos_count_answer

    final_answer = []
    answer: dict[Any, Any] = {}
    photos = 'Sorry, just found photos: 0'
    for cur_hotel in hotel_answer:
        hotel_id = cur_hotel.get("id")
        if int(photo_count) > 0:
            photos = get_hotel_photo(hotel_id, photo_count)

        current_price = "no price"
        ratePlan = cur_hotel.get("ratePlan")
        if not ratePlan:
            answer.get("Price", "no price")
        else:
            price = ratePlan.get("price")
            current_price = price.get("current")

        guest_rating = "no rating"
        guestReviews = cur_hotel.get("guestReviews")
        if not guestReviews:
            answer.get("Guest Rating", "no rating")
        else:
            guest_rating = guestReviews.get("rating")

        check_name = cur_hotel.get("name")
        check_name = str(check_name).replace("'", '💩')
        check_address = cur_hotel["address"].get("streetAddress", "no address")
        check_address = str(check_address).replace("'", '💩')

        answer: dict[str, str | list | Any] = {
            "🏨 Hotel name": check_name,
            "📬 Address": check_address,
            "💲 Price": current_price,
            "💖 Guest rating": guest_rating,
            "🔗 Link": "https://www.hotels.com/ho" + str(hotel_id),
            "📷 Photo": photos
        }
        final_answer.append(answer)

    logger.info(final_answer)

    return final_answer
