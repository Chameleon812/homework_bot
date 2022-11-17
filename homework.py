import logging
import os
import sys
import requests
import telegram
import time
from dotenv import load_dotenv

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

logger = logging.getLogger(__name__)


def send_message(bot, message):
    """Отправка сообщения."""
    bot.send_message(TELEGRAM_CHAT_ID, message)
    logger.info('Cообщение успешно отправлено')


def get_api_answer(current_timestamp):
    """Получение api ответа от Практикума."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    homework_statuses = requests.get(ENDPOINT, headers=HEADERS, params=params)

    if homework_statuses.status_code != 200:
        logger.error('Ответ api не был поучен')
        raise Exception('Ответ api не был поучен')
    else:
        return homework_statuses.json()


def check_response(response):
    """Проверка запроса."""
    if response is None:
        logger.error('Запрос имеет неверное значение')
        raise Exception('Запрос имеет неверное значение')

    if type(response) != dict:
        logger.error('Запрос не является словарем')
        raise TypeError('Запрос не является словарем')

    if response['homeworks'] is None:
        logger.debug('Статус не изменился')
        raise Exception('Статус не изменился')

    if type(response['homeworks']) != list:
        logger.error('homework не является списком')
        raise TypeError('homework не является списком')

    return response['homeworks']


def parse_status(homework):
    """Определения статуса проверки работы."""
    homework_name = homework['homework_name']
    homework_status = homework['status']

    if homework_status in HOMEWORK_STATUSES:
        verdict = HOMEWORK_STATUSES[homework_status]
        return f'Изменился статус проверки работы "{homework_name}". {verdict}'
    else:
        logger.error('Неизвестный статус проверки работы')
        raise ValueError('Неизвестный статус проверки работы')


def check_tokens():
    """Проверка токенов."""
    if all((PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID)):
        return True
    else:
        return False


def main():
    """Основная логика работы бота."""
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    handler = logging.StreamHandler(stream=sys.stdout)
    logger.addHandler(handler)

    if check_tokens() is True:
        logger.info('Все токены на месте')
    else:
        logger.critical('Отсутствует обязательная переменная окружения')
        sys.exit('Заполните все переменные окружения')
    while True:
        try:
            response = get_api_answer(current_timestamp)
            homework = check_response(response)
            if homework != []:
                logger.info('Статус проверки изменен')
                message = parse_status(homework[0])
                send_message(bot, message)
            else:
                logger.debug('Статус не изменился')
                time.sleep(RETRY_TIME)

            current_timestamp = current_timestamp
            time.sleep(RETRY_TIME)

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            send_message(bot, message)
            logger.error(f'Сбой в работе программы: {error}')
            time.sleep(RETRY_TIME)
        else:
            logger.error('Неизвестный сбой, зовите админа')


if __name__ == '__main__':
    main()
