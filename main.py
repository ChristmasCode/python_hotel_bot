from bot import get_start_messages
from models import init_conn


if __name__ == '__main__':
    init_conn()
    get_start_messages()
