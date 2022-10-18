import json
import requests
from api_key import api_key
from loguru import logger
from bot_requests.photos_request import get_hotel_photo

# bestdel
#
#     """
#     Script bestdel.
#         Requested:
#             - City to be searched.
#
#             - Range of prices.
#
#             - The range of distance the hotel is from the center.
#
#             - Number of hotels to withdraw as a result (no more
#             a predetermined maximum).
#
#             - Need to upload and output photos for each hotel («Yes/No»):
#                 - If the answer is positive, the user also enters the number
#                 required photos (no more than the
#                 maxima).
#     """


def get_location(city):
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


def best_get_city(city):
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


def best_get_properties(city_id, number_of_hotels, data_in, data_out,
                        photos_count, price_range_min, price_range_max,
                        city_center_min, city_center_max):
    url = "https://hotels4.p.rapidapi.com/properties/list"

    photos_count_answer = photos_count

    querystring = {
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


def get_hotels(result_hotels, photos_count_answer, city_center_min, city_center_max):
    result = (result_hotels['data']['body']['searchResults']['results'])
    logger.info(result)
    return answer_best_hotel_list(result, photos_count_answer, city_center_min, city_center_max)


def answer_best_hotel_list(hotel_answer, photos_count_answer, city_center_min, city_center_max):
    total_price = "no price"
    photo_count = photos_count_answer

    center_min = city_center_min
    center_max = city_center_max

    final_answer = []
    price_answer = {}
    photos = 'Sorry, just found photos: 0'
    for cur_hotel in hotel_answer:
        hotel_id = cur_hotel.get("id")
        address = cur_hotel.get("address")
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
        check_adress = cur_hotel.get("streetAddress", "no address")
        check_adress = str(check_adress).replace("'", '💩')

        answer = {
            "🏨 Hotel name": check_name,
            "📬 Address": check_adress,
            "💲 Price": current_price,
            "💲 Total price": total_price,
            "💖 Guest rating": guest_rating,
            "🔗 Link": "https://www.hotels.com/ho" + str(hotel_id),
            "📷 Photo": photos
        }
        final_answer.append(answer)

    logger.info(final_answer)

    return final_answer
