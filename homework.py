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
    tokens = {
        PRACTICUM_TOKEN,
        TELEGRAM_TOKEN,
        TELEGRAM_CHAT_ID,
    }
    return all(tokens)


def send_message(bot, message):
    """Отправка сообщения."""
    try:
        logging.debug('Сообщение отправлено')
        bot.send_message(TELEGRAM_CHAT_ID, message)
    except Exception as error:
        logging.error(error)


def get_api_answer(timestamp):
    """Получения данных от API yandex."""
    params = {
        'from_date': timestamp,
    }
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    except requests.RequestException as e:
        logging.error(e)
        raise HTTPError(e)
    if response.status_code != HTTPStatus.OK:
        logging.error(f'Неверный ответ Api {response}')
        raise HTTPError(response)
    if response is None:
        message = 'Доступ к API не получен'
        logging.error(message)
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
    return response.get('homeworks')


def parse_status(homework):
    """Отслеживание статуса домашней работы."""
    if not homework.get('homework_name'):
        logging.warning('Отсутствует имя домашней работы')
        raise KeyError
    else:
        homework_name = homework.get('homework_name')

    homework_status = homework.get('status')
    if 'status' not in homework:
        status = 'Отсутствует статус выполненной работы'
        logging.warning('Отсутствует статус выполненной работы')
        raise KeyError(status)

    verdict = HOMEWORK_VERDICTS.get(homework_status)
    if homework_status not in HOMEWORK_VERDICTS:
        verdict = 'Неверный ключ проверки'
        logging.warning(verdict)
        raise KeyError
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        logging.critical(
            'Oтсутствие обязательных переменных'
            ' окружения во время запуска бота'
        )
        exit()
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = 0
    while True:
        try:
            response = get_api_answer(timestamp)
            homeworks = check_response(response)
            if len(homeworks) == 0:
                message = 'Статус домашнего задания не изменен'
                logging.error(message)
                time.sleep(RETRY_PERIOD)
            if homeworks:
                for homework in homeworks:
                    message = parse_status(homework)
                    send_message(bot, message)
                timestamp = response.get('current_date')
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            send_message(bot, message)
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
