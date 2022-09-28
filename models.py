from peewee import *

conn = SqliteDatabase("history.db")


class BaseModel(Model):
    class Meta:
        database = conn


class User(BaseModel):
    telegram_id = IntegerField(column_name="telegramId", unique=True)

    class Meta:
        table_name = "User"


class Request(BaseModel):
    request = CharField(column_name="request")
    user = ForeignKeyField(User, to_field="telegram_id")

    class Meta:
        table_name = "request"


def init_conn():
    conn.drop_tables([User, Request], safe=True)
    conn.create_tables([User, Request], safe=True)


if __name__ == '__main__':
    init_conn()

