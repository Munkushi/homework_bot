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

RETRY_TIME = 600
ENDPOINT = "https://practicum.yandex.ru/api/user_api/homework_statuses/"
HEADERS = {"Authorization": f"OAuth {PRACTICUM_TOKEN}"}
HOMEWORK_STATUSES = {
    "approved": "Работа проверена: ревьюеру всё понравилось. Ура!",
    "reviewing": "Работа взята на проверку ревьюером.",
    "rejected": "Работа проверена: у ревьюера есть замечания.",
}


def send_message(bot, message):
    """Отправка сообщений."""
    return bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)


def get_api_answer(current_timestamp):
    """Ответ апи."""
    timestamp = current_timestamp or int(time.time())
    params = {"from_date": timestamp}
    response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    if response.status_code != 200:
        raise
    return response.json()


def check_response(response):
    """Ретернит список домашних работ."""
    homework = response["homeworks"]
    if type(homework) != list:
        raise
    return homework


def parse_status(homework):
    """Статус дз."""
    homework_name = homework["homework_name"]
    homework_status = homework["status"]
    verdict = HOMEWORK_STATUSES[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens() -> bool:
    """Провека env-файла."""
    check_file = os.path.exists(".env")
    if (
            check_file is None
            or PRACTICUM_TOKEN is None
            or TELEGRAM_TOKEN is None
            or TELEGRAM_CHAT_ID is None
    ):
        return False
    return True


def main():
    """Основная логика работы бота."""
    logger = logging.getLogger(__name__)
    handler = RotatingFileHandler(
        "my_logger.log",
        maxBytes=50000000,
        backupCount=5
    )
    logger.addHandler(handler)

    bot = Bot(token=TELEGRAM_TOKEN)
    current_timestamp = 1643477528
    while True:
        try:
            response = get_api_answer(current_timestamp)
            logging.debug("Первый запрос к API.")
            сheck_response_1 = response.get("homeworks")
            if сheck_response_1:
                logging.info("Работа найдена. Все хорошо.")
                send_message(bot, parse_status(сheck_response_1[0]))
            current_timestamp = response.get("current_date")
            time.sleep(RETRY_TIME)
        except Exception as error:
            logging.exception(f"У бота случилась какая-то ошибка {error}")
            message = f"Сбой в работе программы: {error}"
            print(message)
            time.sleep(RETRY_TIME)
        else:
            logging.error("Ошибка при запросе к основному API")


if __name__ == "__main__":
    main()
