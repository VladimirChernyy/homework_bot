import logging
import os
import time
from http import HTTPStatus

import requests
import telegram
from dotenv import load_dotenv

from exceptions import HTTPError

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s, %(levelname)s, %(message)s'
)


def check_tokens():
    """Проверка токенов на наличие."""
    flag = True
    tokens = {
        'PRACTICUM_TOKEN': PRACTICUM_TOKEN,
        'TELEGRAM_TOKEN': TELEGRAM_TOKEN,
        'TELEGRAM_CHAT_ID': TELEGRAM_CHAT_ID,
    }
    for token, value in tokens.items():
        if value is None:
            logging.critical(f'Токен {token} отсутствует')
            flag = False
    if flag is not True:
        exit()


def send_message(bot, message):
    """Отправка сообщения."""
    bot.send_message(TELEGRAM_CHAT_ID, message)
    logging.debug(f'Сообщение {message} отправлено')


def get_api_answer(timestamp):
    """Получения данных от API yandex."""
    params = {
        'from_date': timestamp,
    }
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    except requests.RequestException as error:
        logging.error(error)
        raise HTTPError(error)
    if response.status_code != HTTPStatus.OK:
        logging.error(f'Неверный ответ Api {response}')
        raise HTTPError(response)
    return response.json()


def check_response(response):
    """Проверка API на тип данных Python."""
    if not isinstance(response, dict):
        message = 'Неверный тип данных'
        logging.error(message)
        raise TypeError(message)
    if not isinstance(response.get('homeworks'), list):
        message = 'Неверный тип данных ответа'
        logging.error(message)
        raise TypeError(message)


def parse_status(homework):
    """Отслеживание статуса домашней работы."""
    homework_key = (
        'homework_name',
        'status',
    )
    for key in homework_key:
        if key not in homework:
            message = f'Отсутствует {key} домашней работы'
            logging.warning(message)
            raise KeyError(message)
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    verdict = HOMEWORK_VERDICTS.get(homework_status)
    if homework_status not in HOMEWORK_VERDICTS:
        message = f'{homework_status} - это неверный ключ'
        raise KeyError(message)
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    check_tokens()
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = 0
    while True:
        try:
            response = get_api_answer(timestamp)
            check_response(response)
            homeworks = response.get('homeworks')
            if homeworks:
                for homework in homeworks:
                    message = parse_status(homework)
                    send_message(bot, message)
                timestamp = response.get('current_date')
            else:
                message = 'Нет домашних работ'
                logging.debug(message)
        except telegram.TelegramError as error:
            message = f'Ошибка отправки в телеграмм {error}'
            logging.error(message)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            send_message(bot, message)
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
