import json

from models import *


def record(user_id, history_temp):
    temp = str(history_temp).replace("'", '"')
    Request.create(request=temp, user=user_id)


def read(user_id):
    # print(Request.select().where(Request.user == 1170996506))
    query = Request.select().where(Request.user == user_id)
    user_selected = query.dicts().execute()
    # print(user_selected)
    return user_selected
    # return user["request"] # обработать в history
