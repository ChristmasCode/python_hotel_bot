import requests
import json


# def want_photos(answer):
#     if answer == "yes":
#         how_many_photos = input("How many photos? ")
#         while not (how_many_photos.isnumeric() and int(how_many_photos) > 0):
#             print("Enter an integer, a positive number")
#             how_many_photos = input("How many photos? ")
#         return int(how_many_photos)
#     elif answer == "no":
#         return 0
#     else:
#         print("Enter 'yes' or 'no': ")
#         want_photos(input("you want to see photos of hotels? ('yes'/'no'): ").lower())


def get_hotel_photo(hotel_id, photo_count):
    url = "https://hotels4.p.rapidapi.com/properties/get-hotel-photos"

    querystring = {"id": hotel_id}
    answer = []

    headers = {
        "X-RapidAPI-Key": "308a0ecd4dmsh778f749df86bb27p1e009ajsn881d6b34ec98",
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

