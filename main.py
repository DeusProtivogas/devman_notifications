import os
import json
import telegram
import requests
from environs import Env
from time import sleep

env = Env()
env.read_env()


def main():
    api_key = os.environ.get('API_KEY')

    telegram_key = os.environ.get('TELEGRAM_BOT_TOKEN')

    bot = telegram.Bot(token=telegram_key)

    updates = bot.get_updates()
    chat_id = updates[0].message.from_user.id

    long_polling_url = "https://dvmn.org/api/long_polling/"
    headers = {
        'Authorization': f'Token {api_key}',
    }
    params = {}

    timeout_timer = 90

    while True:
        try:
            request = requests.get(
                long_polling_url,
                params=params,
                headers=headers,
                timeout=timeout_timer,
            )

            review = json.loads(request.text).get("new_attempts")[0]

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
        except requests.exceptions.ReadTimeout:
            print("No reviews detected")
        except requests.exceptions.ConnectionError:
            print("No internet connection")
            sleep(timeout_timer)


if __name__ == '__main__':
    main()

