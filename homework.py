import logging
import os
import os.path
import time
from logging.handlers import RotatingFileHandler

import requests
from dotenv import load_dotenv
from telegram import Bot

logging.basicConfig(
    level=logging.DEBUG,
    filename="main.log",
    format="%(asctime)s, %(levelname)s, %(message)s, %(name)s",
)

load_dotenv()

PRACTICUM_TOKEN = os.getenv("PRACTICUM_TOKEN")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

TELEGRAM_RETRY_TIME = os.getenv("TELEGRAM_RETRY_TIME")
ENDPOINT = "https://practicum.yandex.ru/api/user_api/homework_statuses/"
HEADERS = {"Authorization": f"OAuth {PRACTICUM_TOKEN}"}
HOMEWORK_STATUSES = {
    "approved": "Работа проверена: ревьюеру всё понравилось. Ура!",
    "reviewing": "Работа взята на проверку ревьюером.",
    "rejected": "Работа проверена: у ревьюера есть замечания.",
}


def logg():
    """функция логов."""
    logger = logging.getLogger(__name__)
    handler = RotatingFileHandler(
        "my_logger.log",
        maxBytes=50000000,
        backupCount=5
    )
    logger.addHandler(handler)


class StatusError(Exception):
    """ошибка для проверки статуса."""

    pass


class EmtpyHomeworkError(Exception):
    """список дз не пустой."""

    pass


def send_message(bot, message):
    """Отправка сообщений."""
    return bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)


def get_api_answer(current_timestamp):
    """Ответ апи."""
    timestamp = current_timestamp or int(time.time())
    params = {"from_date": timestamp}
    response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    if response.status_code != 200:
        logging.exception("Статус ответа не равен 200.")
        raise StatusError("Статус ответа не равен 200.")
    return response.json()


def check_response(response):
    """Ретернит список домашних работ."""
    homework = response["homeworks"]
    if len(homework) == 0:
        logging.exception("В ответе пустой список.")
        raise EmtpyHomeworkError("Список дз пустой.")
    if type(homework) != list:
        logging.exception("Тип homework = list. Или список дз пустой.")
        raise StatusError("Тип homework = list.")
    else:
        return homework


def parse_status(homework):
    """Статус дз."""
    if "status" not in homework.keys():
        raise EmtpyHomeworkError("В словаре нет таких ключей")
    homework_name = homework["homework_name"]
    homework_status = homework["status"]
    verdict = HOMEWORK_STATUSES[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens() -> bool:
    """Провека env-файла."""
    if (
            PRACTICUM_TOKEN is None
            or TELEGRAM_TOKEN is None
            or TELEGRAM_CHAT_ID is None
    ):
        logging.exception("Отстутствует переменная.")
        return False

    return True


def main():
    """Основная логика работы бота."""
    logg()
    bot = Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    while True:
        try:
            response = get_api_answer(current_timestamp)
            logging.debug("Первый запрос к API.")
            new_hw = response.get("homeworks")
            if new_hw:
                logging.info("Работа найдена. Все хорошо.")
                send_message(bot, parse_status(new_hw[0]))
            current_timestamp = response.get("current_date")
        except Exception as error:
            logging.exception(f"У бота случилась какая-то ошибка {error}")
        finally:
            time.sleep(int(TELEGRAM_RETRY_TIME))


if __name__ == "__main__":
    if check_tokens() is True:
        main()
