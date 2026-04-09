"""CLI-скрипт для получения текущей погоды по названию города."""

import os
import sys
from typing import Optional

import requests
from dotenv import load_dotenv


OPENWEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"


def get_weather(city: str, api_key: str) -> dict:
    """Запрашивает у OpenWeather текущую погоду для указанного города."""
    params = {
        "q": city,
        "appid": api_key,
        "units": "metric",
        "lang": "ru",
    }
    response = requests.get(OPENWEATHER_URL, params=params, timeout=10)
    response.raise_for_status()
    return response.json()


def format_output(data: dict) -> str:
    """Форматирует ответ API в строку для вывода в консоль."""
    temp = data["main"]["temp"]
    description = data["weather"][0]["description"]
    city_name = data.get("name", "")
    return f"{city_name}: {temp:.1f}°C, {description}"


def extract_api_error(response_json: dict) -> Optional[str]:
    """Извлекает текст ошибки API из JSON-ответа, если он есть."""
    message = response_json.get("message")
    if isinstance(message, str) and message.strip():
        return message.strip()
    return None


def main() -> int:
    """Точка входа CLI: читает аргументы, вызывает API и обрабатывает ошибки."""
    load_dotenv()
    api_key = os.getenv("OPENWEATHER_API_KEY")

    if not api_key:
        print("Ошибка: не найден OPENWEATHER_API_KEY в файле .env")
        return 1

    if len(sys.argv) < 2:
        print("Использование: python weather.py <город>")
        return 1

    city = " ".join(sys.argv[1:]).strip()
    if not city:
        print("Ошибка: укажите название города")
        return 1

    try:
        weather_data = get_weather(city, api_key)
        print(format_output(weather_data))
        return 0
    except requests.exceptions.HTTPError as error:
        # Ошибки HTTP обрабатываем отдельно, чтобы показать понятное сообщение.
        response = error.response
        if response is not None:
            try:
                response_json = response.json()
            except ValueError:
                response_json = {}

            status_code = response.status_code
            api_message = extract_api_error(response_json)

            if status_code == 404:
                print(f"Ошибка: город '{city}' не найден.")
                return 1

            if api_message:
                print(f"Ошибка API ({status_code}): {api_message}")
                return 1

            print(f"Ошибка API: HTTP {status_code}")
            return 1

        print("Ошибка: не удалось получить ответ от API.")
        return 1
    except requests.exceptions.RequestException as error:
        # Сюда попадают сетевые сбои: timeout, проблемы DNS, обрыв соединения.
        print(f"Ошибка сети: {error}")
        return 1
    except (KeyError, IndexError, TypeError, ValueError):
        print("Ошибка: получен неожиданный формат ответа от API.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
