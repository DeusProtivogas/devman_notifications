import os
import json
import telegram
import traceback
import requests
from environs import Env
from time import sleep
import logging

logger = logging.getLogger("Telegram logger")


class TelegramLogsHandler(logging.Handler):

    def __init__(self, tg_bot, chat_id):
        super().__init__()
        logging.basicConfig(format="%(process)d %(levelname)s %(message)s")
        self.chat_id = chat_id
        self.tg_bot = tg_bot

    def emit(self, record):
        log_entry = self.format(record)
        self.tg_bot.send_message(chat_id=self.chat_id, text=log_entry)


def main():
    env = Env()
    env.read_env()

    api_key = os.environ.get('DEVMAN_API_KEY')

    telegram_key = os.environ.get('TELEGRAM_BOT_TOKEN')

    bot = telegram.Bot(token=telegram_key)

    updates = bot.get_updates()
    chat_id = updates[0].message.from_user.id

    logger.addHandler(TelegramLogsHandler(bot, chat_id))

    logger.info("Бот запущен")

    long_polling_url = "https://dvmn.org/api/long_polling/"
    headers = {
        'Authorization': f'Token {api_key}',
    }
    params = {}

    timeout_timer = 3

    while True:
        try:
            response = requests.get(
                long_polling_url,
                params=params,
                headers=headers,
                timeout=timeout_timer,
            )

            response.raise_for_status()

            attempts_status = response.json()

            if attempts_status['status'] == 'timeout':
                params = {'timestamp': attempts_status['timestamp_to_request']}
                continue

            review = attempts_status.get("new_attempts")[0]

            timestamp = review.get("timestamp")
            params = {
                'timestamp ': timestamp,
            }

            lesson_title = review.get("lesson_title")
            is_negative = review.get("is_negative")
            lesson_url = review.get("lesson_url")

            message = f"У Вас проверили работу <<{lesson_title}>>\nПо ссылке {lesson_url}\n\n"
            message += "К сожалению, в ней нашлись ошибки" if is_negative else "Все хорошо! Работа принята!"

            bot.send_message(
                chat_id=chat_id,
                text=message,
            )
        except requests.exceptions.HTTPError:
            print("Bad request")
            logger.warning("Bad request")
        except requests.exceptions.ReadTimeout:
            continue
        except requests.exceptions.ConnectionError:
            print("No internet connection")
            logger.warning("No internet connection")
            sleep(timeout_timer)
        except Exception as error:
            logger.error(traceback.format_exc())
            sleep(timeout_timer)



if __name__ == '__main__':
    logger.setLevel(logging.INFO)
    main()

