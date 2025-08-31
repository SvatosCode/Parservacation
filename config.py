# Конфигурационный файл для Telegram Job Parser Bot

import os
from dotenv import load_dotenv

# Загрузка переменных окружения из .env файла
load_dotenv()

# Telegram Bot API токен
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# ID чата или канала для отправки вакансий
TARGET_CHAT_ID = os.getenv('TARGET_CHAT_ID')

# Настройки парсинга
PARSING_INTERVAL = 3600  # Интервал парсинга в секундах (по умолчанию 1 час)

# Сайты для парсинга вакансий
JOB_SITES = {
    'hh.ru': {
        'base_url': 'https://hh.ru/search/vacancy',
        'params': {
            'text': '{query}',  # Будет заменено на поисковый запрос
            'area': '1',       # Код региона (1 - Москва)
            'per_page': '100'  # Количество вакансий на странице
        }
    },
    'habr.com': {
        'base_url': 'https://career.habr.com/vacancies',
        'params': {
            'q': '{query}',     # Будет заменено на поисковый запрос
            'type': 'all',     # Тип вакансии
            'page': '1'        # Номер страницы
        }
    }
    # Можно добавить другие сайты по аналогии
}

# Ключевые слова для поиска вакансий
SEARCH_QUERIES = ['Python', 'Data Scientist', 'Machine Learning', 'Backend Developer']

# Фильтры для вакансий
FILTERS = {
    'keywords': ['junior', 'middle', 'senior', 'remote'],  # Ключевые слова для фильтрации
    'exclude_keywords': ['1+ years', '3+ years'],           # Исключающие ключевые слова
    'min_salary': 0                                         # Минимальная зарплата
}