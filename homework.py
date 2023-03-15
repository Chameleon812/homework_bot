import logging
import os
import sys
import time
from http import HTTPStatus

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
    'approved': 'The work is checked: the reviewer liked everything. Hooray!',
    'reviewing': 'The work was taken for verification by the reviewer.',
    'rejected': 'The work has been checked: the reviewer has comments.'
}

logger = logging.getLogger(__name__)


def send_message(bot, message: str) -> None:
    """Sending a message."""
    try:
        logger.info('Attempt to send a message')
        bot.send_message(TELEGRAM_CHAT_ID, message)
    except telegram.error.TelegramError:
        logger.error(f'Message not sent: "{message}"')
    else:
        logger.debug('Message sent')


def get_api_answer(current_timestamp: int) -> dict:
    """Getting an api response from the Workshop."""
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
                'The server did not send api. Check the parameters:'
                f'status_code: {check_status_code}, '
                f'reason: {check_reason}, '
                f'text: {check_text}, '
                f'endpoint: {check_endpoint}, '
                f'headers: {check_headers}, '
            )
    except requests.RequestException:
        raise HardException('Error getting api')


def check_response(response: dict) -> list:
    """Request validation."""
    if not isinstance(response, dict):
        raise TypeError('Query is not a dictionary')

    homeworks = response.get('homeworks')
    current_date = response.get('current_date')

    if not isinstance(homeworks, list):
        raise TypeError('homeworks is not a list')

    if not isinstance(current_date, int):
        raise TypeError('The server sent an unknown date format')
    return homeworks


def parse_status(homework: dict) -> str:
    """Determining the status of a job review."""
    if 'homework_name' not in homework:
        raise KeyError('Missing key "homework_name"')
    if 'status' not in homework:
        raise KeyError('Missing key "status"')

    homework_name = homework['homework_name']
    homework_status = homework['status']

    if homework_status not in HOMEWORK_VERDICTS:
        raise ValueError('Unknown check status')

    verdict = HOMEWORK_VERDICTS[f'{homework_status}']
    return f'Job verification status changed "{homework_name}". {verdict}'


def check_tokens() -> bool:
    """Checking tokens."""
    return all((PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID))


def main() -> None:
    """The main logic of the bot."""
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    old_status_message = ''
    old_error_message = ''

    logging.basicConfig(
        format='%(asctime)s | %(levelname)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        level=logging.DEBUG,
        handlers=[logging.StreamHandler(stream=sys.stdout),
                  logging.FileHandler(filename='list.log')]
    )

    if check_tokens() is False:
        logger.critical('Missing required environment variable')
        sys.exit('Fill in all environment variables')
    while True:
        logger.info('All tokens are in place')
        try:
            response = get_api_answer(current_timestamp)
            homework = check_response(response)
            if not homework:
                logger.debug('Status has not changed')
            else:
                status_message = parse_status(homework[0])
                if status_message != old_status_message:
                    logger.info('Check status changed')
                    send_message(bot, status_message)
                    old_status_message = status_message

            current_timestamp = response.get('current_timestamp')

        except EasyException as error:
            logger.error(f'Regular deviation from the scenario: {error}')

        except Exception as error:
            error_message = f'Program crash: {error}'
            logger.error(error, exc_info=error)
            if error_message != old_error_message:
                send_message(bot, error_message)
                old_error_message = error_message

        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
