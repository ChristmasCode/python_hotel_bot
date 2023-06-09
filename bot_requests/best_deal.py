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


def best_get_city(city: str) -> dict:
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


def best_get_properties(city_id: int,
                        number_of_hotels: int,
                        data_in: str,
                        data_out: str,
                        photos_count: int,
                        price_range_min: int | float,
                        price_range_max: int | float,
                        city_center_min: int | float,
                        city_center_max: int | float) -> list:
    url = "https://hotels4.p.rapidapi.com/properties/list"

    photos_count_answer = photos_count

    querystring: dict[str | Any, int | str | float | Any] = {
        "destinationId": city_id,
        "pageNumber": "1",
        "pageSize": number_of_hotels,
        "checkIn": data_in,
        "checkOut": data_out,
        "priceMin": price_range_min,
        "priceMax": price_range_max,
        "adults1": "1",
        "sortOrder": "PRICE",
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
    return get_hotels(result, photos_count_answer, city_center_min, city_center_max)


def get_hotels(result_hotels: dict,
               photos_count_answer: int,
               city_center_min: int | float,
               city_center_max: int | float) -> Any:
    result = (result_hotels['data']['body']['searchResults']['results'])
    logger.info(result)
    return answer_best_hotel_list(result, photos_count_answer, city_center_min, city_center_max)


def answer_best_hotel_list(hotel_answer: dict,
                           photos_count_answer: int,
                           city_center_min: int | float,
                           city_center_max: int | float) -> list:
    total_price = "no price"
    photo_count = photos_count_answer

    center_min = city_center_min
    center_max = city_center_max

    final_answer = []
    price_answer = {}
    photos = 'Sorry, just found photos: 0'
    for cur_hotel in hotel_answer:
        hotel_id = cur_hotel.get("id")
        city_center = cur_hotel["landmarks"][0]["distance"]
        if center_min > city_center > center_max:
            pass
        if int(photo_count) > 0:
            photos = get_hotel_photo(hotel_id, photo_count)

        current_price = "no price"
        ratePlan = cur_hotel.get("ratePlan")
        if not ratePlan:
            price_answer.get("Price", "no price")
            price_answer.get("Total price", "no price")
        else:
            price = ratePlan.get("price")
            current_price = price.get("current")
            total_price = price.get("fullyBundledPricePerStay")

        total_price = total_price.split(" ")[1]
        guest_rating = "no rating"
        guestReviews = cur_hotel.get("guestReviews")
        if not guestReviews:
            price_answer.get("Guest Rating", "no rating")
        else:
            guest_rating = guestReviews.get("rating")

        check_name = cur_hotel.get("name")
        check_name = str(check_name).replace("'", '💩')
        check_address = cur_hotel["address"].get("streetAddress", "no address")
        check_address = str(check_address).replace("'", '💩')

        answer = {
            "🏨 Hotel name": check_name,
            "📬 Address": check_address,
            "💲 Price": current_price,
            "💲 Total price": total_price,
            "💖 Guest rating": guest_rating,
            "🔗 Link": "https://www.hotels.com/ho" + str(hotel_id),
            "📷 Photo": photos
        }
        final_answer.append(answer)

    logger.info(final_answer)

    return final_answer
