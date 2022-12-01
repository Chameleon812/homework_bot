import os
import sys
import time

from http import HTTPStatus
import logging
import requests
import telegram

from dotenv import load_dotenv
from exceptions import EasyException, HardException

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD: int = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

logger = logging.getLogger(__name__)


def send_message(bot, message: str) -> None:
    """Отправка сообщения."""
    try:
        logger.info('Попытка отправки сообщения')
        bot.send_message(TELEGRAM_CHAT_ID, message)
    except telegram.error.TelegramError:
        logger.error('Cообщение не отправлено')
    else:
        logger.debug('Сообщение отправлено')


def get_api_answer(current_timestamp: int) -> dict:
    """Получение api ответа от Практикума."""
    timestamp = current_timestamp
    params = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
        if response.status_code == HTTPStatus.OK:
            return response.json()
        else:
            check_status_code = response.status_code
            check_reason = response.reason
            check_text = response.text
            check_endpoint = response.url
            check_headers = response.headers

            raise HardException(
                'Сервер не отправил api.Проверье параметры:'
                f'status_code: {check_status_code}, '
                f'reason: {check_reason}, '
                f'text: {check_text}, '
                f'endpoint: {check_endpoint}, '
                f'headers: {check_headers}, '
            )
    except requests.RequestException:
        'Ошибка при получении api'


def check_response(response: dict) -> list:
    """Проверка запроса."""
    if not isinstance(response, dict):
        raise TypeError('Запрос не является словарем')
    if response is None:
        raise ValueError('Запрос имеет неверное значение')

    homeworks = response.get('homeworks')
    current_date = response.get('current_date')

    if not isinstance(homeworks, list):
        raise TypeError('homeworks не является списком')

    if current_date is None:
        raise EasyException('Сервер не прислал отсечку времени')

    if not isinstance(current_date, int):
        raise TypeError('Сервер прислал неизвестный формат даты')
    return homeworks


def parse_status(homework: dict) -> str:
    """Определения статуса проверки работы."""
    if 'homework_name' not in homework:
        raise KeyError('Отсутсвут ключ "homework_name"')
    if 'status' not in homework:
        raise KeyError('Отсутсвут ключ "status"')

    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')

    if homework_status not in HOMEWORK_VERDICTS:
        raise ValueError('Неизвестный статус проверки')

    verdict = HOMEWORK_VERDICTS.get(homework_status)
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens() -> bool:
    """Проверка токенов."""
    return all((PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID))


def main() -> None:
    """Основная логика работы бота."""
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())

    logging.basicConfig(
        format='%(asctime)s | %(levelname)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        level=logging.DEBUG,
        handlers=[logging.StreamHandler(stream=sys.stdout),
                  logging.FileHandler(filename='list.log')]
    )

    if check_tokens() is False:
        logger.critical('Отсутствует обязательная переменная окружения')
        sys.exit('Заполните все переменные окружения')
    while True:
        logger.info('Все токены на месте')
        try:
            response = get_api_answer(current_timestamp)
            homework = check_response(response)
            if not homework:
                logger.debug('Статус не изменился')
            else:
                message = parse_status(homework[0])
                logger.info('Статус проверки изменен')
                send_message(bot, message)
            current_timestamp = response.get('current_timestamp')

        except HardException as error:
            message = f'Сбой в работе программы: {error}'
            send_message(bot, message)
            logger.error(error, exc_info=error)

        except EasyException as error:
            logger.debug(f'Штатное отклонение от сценария: {error}')

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            send_message(bot, message)
            logger.error(error, exc_info=error)

        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
