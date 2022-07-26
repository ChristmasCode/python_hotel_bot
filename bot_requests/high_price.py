import json
import requests
from photos_request import want_photos, get_hotel_photo


def high_price():

    """highprice.
        Requested:
            - City to be searched.

            - Number of hotels to withdraw as a result (no more
            a predetermined maximum).

            - Need to upload and output photos for each hotel («Yes/No»):
                - If the answer is positive, the user also enters the number
                required photos (no more than the
                maxima).
    """

    def get_location():

        url = "https://hotels4.p.rapidapi.com/locations/v2/search"

        querystring = {
            "query": input('Enter the city where you want to search: '),
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

        return result

    def get_city():
        result_location = get_location()
        list_suggestions = result_location.get('suggestions')
        group_city = list_suggestions[0]
        # list_city_name = [name.get('name') for name in group_city.get('entities')] # returns a list of cities(
        # city districts)
        list_destinationId = [destinationId.get('destinationId') for destinationId in group_city.get('entities')]  #
        # returns the ID of cities(city districts)
        result = list_destinationId[0]

        return result

    def get_properties():
        url = "https://hotels4.p.rapidapi.com/properties/list"

        querystring = {
            "destinationId": get_city(),
            "pageNumber": "1",
            "pageSize": "3",
            "checkIn": "2022-08-08",
            "checkOut": "2022-08-15",
            "adults1": "1",
            "sortOrder": "PRICE_HIGHEST_FIRST",
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

    def get_hotels():

        result_hotels = get_properties()

        result = (result_hotels['data']['body']['searchResults']['results'])
        # with open('hotel_answer', 'w+') as file:
        #     json.dump(result, file, indent=4)

        return result

    def answer_hotel_list():

        hotel_answer = get_hotels()

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
                "Guest rating": guest_rating
            }
            for answer_key, answer_value in answer.items():
                print(answer_key + ":", answer_value)

            if photo_count > 0:
                get_hotel_photo(hotel_id, photo_count)

    answer_hotel_list()


high_price()
