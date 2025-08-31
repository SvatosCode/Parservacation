# Основной файл Telegram Job Parser Bot

import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.utils.markdown import hbold, hlink, hcode
from aiogram.dispatcher.filters import Command
from datetime import datetime
import json
import os

from config import TELEGRAM_BOT_TOKEN, TARGET_CHAT_ID, SEARCH_QUERIES, PARSING_INTERVAL
from parser import JobParser

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Инициализация бота и диспетчера
bot = Bot(token=TELEGRAM_BOT_TOKEN, parse_mode=types.ParseMode.HTML)
dp = Dispatcher(bot)

# Инициализация парсера вакансий
job_parser = JobParser()

# Файл для хранения отправленных вакансий
SENT_JOBS_FILE = 'sent_jobs.json'

# Загрузка отправленных вакансий из файла
def load_sent_jobs():
    if os.path.exists(SENT_JOBS_FILE):
        try:
            with open(SENT_JOBS_FILE, 'r', encoding='utf-8') as f:
                return set(json.load(f))
        except Exception as e:
            logger.error(f"Ошибка при загрузке отправленных вакансий: {e}")
    return set()

# Сохранение отправленных вакансий в файл
def save_sent_jobs(sent_jobs):
    try:
        with open(SENT_JOBS_FILE, 'w', encoding='utf-8') as f:
            json.dump(list(sent_jobs), f)
    except Exception as e:
        logger.error(f"Ошибка при сохранении отправленных вакансий: {e}")

# Обработчик команды /start
@dp.message_handler(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        f"Привет, {message.from_user.first_name}! 👋\n\n"
        f"Я бот для парсинга вакансий. Я буду автоматически собирать вакансии "
        f"с популярных сайтов и отправлять их в настроенный чат или канал.\n\n"
        f"Доступные команды:\n"
        f"/start - Показать это сообщение\n"
        f"/help - Показать справку\n"
        f"/parse - Запустить парсинг вакансий вручную\n"
        f"/status - Показать статус бота"
    )

# Обработчик команды /help
@dp.message_handler(Command("help"))
async def cmd_help(message: types.Message):
    await message.answer(
        f"📚 <b>Справка по использованию бота</b>\n\n"
        f"Этот бот автоматически собирает вакансии с настроенных сайтов "
        f"и отправляет их в указанный чат или канал.\n\n"
        f"<b>Доступные команды:</b>\n"
        f"/start - Начать работу с ботом\n"
        f"/help - Показать эту справку\n"
        f"/parse - Запустить парсинг вакансий вручную\n"
        f"/status - Показать статус бота и настройки парсинга\n\n"
        f"<b>Настройки бота</b> хранятся в файле config.py и включают:\n"
        f"- Список сайтов для парсинга\n"
        f"- Поисковые запросы\n"
        f"- Фильтры для вакансий\n"
        f"- Интервал автоматического парсинга"
    )

# Обработчик команды /status
@dp.message_handler(Command("status"))
async def cmd_status(message: types.Message):
    await message.answer(
        f"📊 <b>Статус бота</b>\n\n"
        f"<b>Активные поисковые запросы:</b>\n{hcode(', '.join(SEARCH_QUERIES))}\n\n"
        f"<b>Интервал парсинга:</b> {PARSING_INTERVAL // 60} минут\n\n"
        f"<b>Целевой чат для отправки:</b> {TARGET_CHAT_ID}\n\n"
        f"<b>Количество отслеживаемых вакансий:</b> {len(load_sent_jobs())}\n\n"
        f"<b>Последнее обновление:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )

# Обработчик команды /parse
@dp.message_handler(Command("parse"))
async def cmd_parse(message: types.Message):
    await message.answer("🔍 Запускаю парсинг вакансий...")
    
    try:
        # Запуск парсинга вакансий
        jobs = await parse_jobs()
        
        if jobs:
            await message.answer(f"✅ Парсинг завершен. Найдено {len(jobs)} новых вакансий.")
        else:
            await message.answer("ℹ️ Парсинг завершен. Новых вакансий не найдено.")
    except Exception as e:
        logger.error(f"Ошибка при выполнении команды /parse: {e}")
        await message.answer(f"❌ Произошла ошибка при парсинге вакансий: {str(e)}")

# Функция для форматирования вакансии в HTML
def format_job_message(job):
    message = (
        f"🔍 <b>{hbold(job['title'])}</b>\n\n"
        f"🏢 Компания: {job['company']}\n"
        f"💰 Зарплата: {job['salary']}\n\n"
    )
    
    if job['description']:
        # Ограничиваем описание до 200 символов
        description = job['description'][:200] + '...' if len(job['description']) > 200 else job['description']
        message += f"📝 {description}\n\n"
    
    message += (
        f"🌐 Источник: {job['source']}\n"
        f"🔎 Запрос: {job['query']}\n"
        f"📅 Дата: {datetime.fromisoformat(job['timestamp']).strftime('%Y-%m-%d %H:%M')}\n\n"
    )
    
    if job['link']:
        message += f"🔗 {hlink('Ссылка на вакансию', job['link'])}"
    
    return message

# Асинхронная функция для парсинга вакансий
async def parse_jobs():
    # Загрузка списка уже отправленных вакансий
    sent_jobs = load_sent_jobs()
    new_jobs = []
    
    # Парсинг вакансий для каждого поискового запроса
    for query in SEARCH_QUERIES:
        # Запускаем парсинг в отдельном потоке, чтобы не блокировать асинхронный цикл событий
        loop = asyncio.get_event_loop()
        jobs = await loop.run_in_executor(None, lambda: job_parser.parse_all_sites(query))
        
        for job in jobs:
            # Создаем уникальный идентификатор вакансии
            job_id = f"{job['source']}_{job['link']}"
            
            # Проверяем, не была ли вакансия уже отправлена
            if job_id not in sent_jobs:
                # Форматируем сообщение с вакансией
                message = format_job_message(job)
                
                try:
                    # Отправляем сообщение в целевой чат
                    await bot.send_message(chat_id=TARGET_CHAT_ID, text=message)
                    logger.info(f"Отправлена новая вакансия: {job['title']} ({job['source']})")
                    
                    # Добавляем вакансию в список отправленных
                    sent_jobs.add(job_id)
                    new_jobs.append(job)
                    
                    # Небольшая задержка между отправками сообщений
                    await asyncio.sleep(0.5)
                except Exception as e:
                    logger.error(f"Ошибка при отправке вакансии: {e}")
    
    # Сохраняем обновленный список отправленных вакансий
    save_sent_jobs(sent_jobs)
    
    return new_jobs

# Функция для периодического парсинга вакансий
async def scheduled_parsing():
    while True:
        try:
            logger.info("Запуск запланированного парсинга вакансий")
            await parse_jobs()
            logger.info(f"Следующий парсинг запланирован через {PARSING_INTERVAL // 60} минут")
        except Exception as e:
            logger.error(f"Ошибка при запланированном парсинге: {e}")
        
        # Ждем указанный интервал перед следующим парсингом
        await asyncio.sleep(PARSING_INTERVAL)

# Запуск бота
async def main():
    try:
        # Запуск задачи периодического парсинга
        asyncio.create_task(scheduled_parsing())
        
        # Вывод информации о запуске бота
        logger.info("Бот запущен")
        
        # Запуск поллинга бота
        await dp.start_polling()
    finally:
        await bot.session.close()

if __name__ == '__main__':
    try:
        # Запуск основной функции
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Бот остановлен")