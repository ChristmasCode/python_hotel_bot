from models import *

conn = SqliteDatabase("history.db")


def record(user_id, history_temp):
    Request.create(request=history_temp, user=user_id)


def read(user_id):
    query = Request.select(Request.request).where(Request.user == user_id)
    user_selected = query.dicts().execute()
    return user_selected


if __name__ == '__main__':
    init_conn()
    read(1170996506)
