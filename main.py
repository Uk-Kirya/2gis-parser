import telebot
import requests
import pandas as pd
import json

API_KEY = '73e483cc-a78a-42b3-a250-2ff048c4a71d'
BOT_TOKEN = '7039231582:AAEFRQBZU_adEZrp_SAN31lzhk1HzLNIalk'

bot = telebot.TeleBot(BOT_TOKEN)


def get_city_id(value: str) -> int:
    """
    Функция получения ID города по его названию
    :param value: Название города (str)
    :return: ID города (int)
    """
    url = f'https://catalog.api.2gis.com/2.0/region/search?q={value}&key={API_KEY}'
    response = requests.get(url)
    city_id = response.json()
    return city_id['result']['items'][0]['id']


def get_companies(city: int, query: str) -> str:
    """
    Функция получения данных по запрашиваемым компаниям
    :param city: ID города, полученный от get_city_id() (int)
    :param query: Искомый запрос (str)
    :return: список объектов
    """
    url = 'https://catalog.api.2gis.com/3.0/items'
    params = {
        'key': API_KEY,
        'region_id': city,
        'q': query,
        'fields': 'items.contacts',
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        return data
    else:
        return f'Возникла ошибка формирования списка'


def create_xls(data: str, city: str, companies: str) -> str:
    """
    Функция создания файла excel, куда будут в дальнейшем записываться данные
    :param data: информация для записи (str)
    :param city: город поиска (str)
    :param companies: искомый объект (str)
    :return: путь к созданному файлу
    """
    rows = []
    for item in data['result']['items']:
        row = {
            'Город': city,
            'Район': '-',  # Данные о районе пока отсутствуют
            'Категория': companies,
            'Название компании': item.get('name', '-'),
            'Адрес компании': item.get('address_name', '-'),
            'Телефон компании': '-',  # Данные о телефоне пока отсутствуют
            'Почта компании': '-'  # Данные о почте пока отсутствуют
        }
        rows.append(row)

    df = pd.DataFrame(rows)
    file_path = f'{city}_{companies}.xlsx'
    df.to_excel(file_path, index=False)
    return file_path


@bot.message_handler(commands=['start'])
def start(message):
    user = message.from_user
    bot.reply_to(message, f'Привет, {user.first_name}! Я бот для поиска компаний.\n\nПожалуйста, укажите город.')
    bot.register_next_step_handler(message, process_place)


def new_search(message):
    bot.send_message(message.chat.id, 'Пожалуйста, укажите город.')
    bot.register_next_step_handler(message, process_place)


def process_place(message):
    """
    1. Обработка города, полученного от start()
    2. Запрос тематики поиска
    """
    city = message.text
    bot.reply_to(message, 'Теперь укажите тематику (например, "кафе").')
    bot.register_next_step_handler(message, process_query_step, city)


def process_query_step(message, city):
    """
    1. Обработка тематики поиска
    2. Запрос информации по API
    3. Сохранение информации в созданный excel файл в функции create_xls()
    """
    place = message.text
    city_id = get_city_id(city)
    companies = get_companies(city_id, place)
    file_path = create_xls(companies, city, place)
    bot.reply_to(message, 'Информация сохранена. Формирую список ...')
    with open('json_file.json', 'w') as file:
        json.dump(companies, file, ensure_ascii=False, indent=4)

    with open(file_path, 'rb') as f:
        bot.send_document(message.chat.id, f)

    bot.send_message(message.chat.id, f'Для нового поиска, нажмите /start')
    bot.register_next_step_handler(message, new_search)


if __name__ == "__main__":
    bot.polling()
