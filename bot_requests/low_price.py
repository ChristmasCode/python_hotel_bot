import json
import requests
from loguru import logger
from bot_requests.photos_request import want_photos, get_hotel_photo


# low_price:
#
#     """
#     Script lowprice.
#         Requested:
#             - City to be searched.
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
        "X-RapidAPI-Key": "308a0ecd4dmsh778f749df86bb27p1e009ajsn881d6b34ec98",
        "X-RapidAPI-Host": "hotels4.p.rapidapi.com"
    }

    response = requests.request("GET", url, headers=headers, params=querystring, timeout=10)
    result = json.loads(response.text)

    # with open('location_answer', 'w+') as file:
    #     json.dump(result, file, indent=4)
    logger.info(result)
    return result


def get_city(city):
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


def lowprice_get_properties(city_id, number_of_hotels, data_in, data_out):
    url = "https://hotels4.p.rapidapi.com/properties/list"

    querystring = {
        "destinationId": city_id,
        "pageNumber": "1",
        "pageSize": number_of_hotels,
        "checkIn": data_in,
        "checkOut": data_out,
        "adults1": "1",
        "sortOrder": "PRICE",
        "locale": "en_US",
        "currency": "USD"
    }

    headers = {
        "X-RapidAPI-Key": "308a0ecd4dmsh778f749df86bb27p1e009ajsn881d6b34ec98",
        "X-RapidAPI-Host": "hotels4.p.rapidapi.com"
    }

    response = requests.request("GET", url, headers=headers, params=querystring, timeout=60)
    result = json.loads(response.text)

    # with open('location_answer', 'w+') as file:
    #     json.dump(result, file, indent=4)
    logger.info(result)
    return get_hotels(result)


def get_hotels(result_hotels):

    result = (result_hotels['data']['body']['searchResults']['results'])
    # with open('hotel_answer', 'w+') as file:
    #     json.dump(result, file, indent=4)

    return result


def answer_low_hotel_list(hotel_answer):

    photo_count = want_photos(input("you want to see photos of hotels? ('yes'/'no'): ").lower())

    answer = {}
    for cur_hotel in hotel_answer:
        hotel_id = cur_hotel.get("id")
        address = cur_hotel.get("address")

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

        answer = {
            "Hotel name": cur_hotel.get("name"),
            "Address": address.get("streetAddress", "no address"),
            "Price": current_price,
            "Guest rating": guest_rating,
            "Link": "https://www.hotels.com/ho" + str(hotel_id)
        }
        for answer_key, answer_value in answer.items():
            print(answer_key + ":", answer_value)

        if photo_count > 0:
            get_hotel_photo(hotel_id, photo_count)

    # answer_low_hotel_list()

# low_price()
