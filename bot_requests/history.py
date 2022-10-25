from models import *

conn = SqliteDatabase("history.db")


def record(history_temp, user_id, history_time, history_command):
    Request.create(request=history_temp, user=user_id, current_time=history_time, input_command=history_command)


def read(user_id):
    query = Request.select(Request.request).where(Request.user == user_id)
    user_selected = query.dicts().execute()
    return user_selected


def read_time(user_id):
    query = Request.select(Request.current_time).where(Request.user == user_id)
    user_selected = query.dicts().execute()
    return user_selected


def read_command(user_id):
    query = Request.select(Request.input_command).where(Request.user == user_id)
    user_selected = query.dicts().execute()
    return user_selected


if __name__ == '__main__':
    init_conn()
    read(1170996506)
