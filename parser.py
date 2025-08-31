# Модуль для парсинга вакансий с различных сайтов

import requests
from bs4 import BeautifulSoup
import time
import logging
from datetime import datetime
from config import JOB_SITES, FILTERS

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("parser.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class JobParser:
    """Класс для парсинга вакансий с различных сайтов"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                          '(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.jobs_cache = set()  # Кэш для хранения уже обработанных вакансий
    
    def parse_hh_ru(self, query):
        """Парсинг вакансий с hh.ru"""
        site_config = JOB_SITES['hh.ru']
        params = site_config['params'].copy()
        params['text'] = params['text'].format(query=query)
        
        jobs = []
        try:
            response = self.session.get(site_config['base_url'], params=params)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            vacancy_items = soup.find_all('div', {'class': 'vacancy-serp-item'})
            
            for item in vacancy_items:
                try:
                    # Извлечение данных о вакансии
                    title_element = item.find('a', {'data-qa': 'vacancy-serp__vacancy-title'})
                    title = title_element.text.strip() if title_element else 'Нет названия'
                    link = title_element['href'] if title_element else None
                    
                    company_element = item.find('a', {'data-qa': 'vacancy-serp__vacancy-employer'})
                    company = company_element.text.strip() if company_element else 'Компания не указана'
                    
                    description_element = item.find('div', {'data-qa': 'vacancy-serp__vacancy_snippet_responsibility'})
                    description = description_element.text.strip() if description_element else ''
                    
                    salary_element = item.find('span', {'data-qa': 'vacancy-serp__vacancy-compensation'})
                    salary = salary_element.text.strip() if salary_element else 'Зарплата не указана'
                    
                    # Создание объекта вакансии
                    job = {
                        'title': title,
                        'company': company,
                        'description': description,
                        'salary': salary,
                        'link': link,
                        'source': 'hh.ru',
                        'query': query,
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    # Проверка на дубликаты и применение фильтров
                    job_id = f"{job['source']}_{job['link']}"
                    if job_id not in self.jobs_cache and self._apply_filters(job):
                        jobs.append(job)
                        self.jobs_cache.add(job_id)
                        
                except Exception as e:
                    logger.error(f"Ошибка при обработке вакансии на hh.ru: {e}")
            
            logger.info(f"Найдено {len(jobs)} новых вакансий на hh.ru по запросу '{query}'")
            
        except Exception as e:
            logger.error(f"Ошибка при парсинге hh.ru: {e}")
        
        return jobs
    
    def parse_habr_career(self, query):
        """Парсинг вакансий с career.habr.com"""
        site_config = JOB_SITES['habr.com']
        params = site_config['params'].copy()
        params['q'] = params['q'].format(query=query)
        
        jobs = []
        try:
            response = self.session.get(site_config['base_url'], params=params)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            vacancy_items = soup.find_all('div', {'class': 'vacancy-card'})
            
            for item in vacancy_items:
                try:
                    # Извлечение данных о вакансии
                    title_element = item.find('a', {'class': 'vacancy-card__title-link'})
                    title = title_element.text.strip() if title_element else 'Нет названия'
                    link = 'https://career.habr.com' + title_element['href'] if title_element and title_element.has_attr('href') else None
                    
                    company_element = item.find('div', {'class': 'vacancy-card__company-title'})
                    company = company_element.text.strip() if company_element else 'Компания не указана'
                    
                    description_element = item.find('div', {'class': 'vacancy-card__skills'})
                    description = description_element.text.strip() if description_element else ''
                    
                    salary_element = item.find('div', {'class': 'vacancy-card__salary'})
                    salary = salary_element.text.strip() if salary_element else 'Зарплата не указана'
                    
                    # Создание объекта вакансии
                    job = {
                        'title': title,
                        'company': company,
                        'description': description,
                        'salary': salary,
                        'link': link,
                        'source': 'habr.com',
                        'query': query,
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    # Проверка на дубликаты и применение фильтров
                    job_id = f"{job['source']}_{job['link']}"
                    if job_id not in self.jobs_cache and self._apply_filters(job):
                        jobs.append(job)
                        self.jobs_cache.add(job_id)
                        
                except Exception as e:
                    logger.error(f"Ошибка при обработке вакансии на habr.com: {e}")
            
            logger.info(f"Найдено {len(jobs)} новых вакансий на habr.com по запросу '{query}'")
            
        except Exception as e:
            logger.error(f"Ошибка при парсинге habr.com: {e}")
        
        return jobs
    
    def parse_all_sites(self, query):
        """Парсинг вакансий со всех настроенных сайтов"""
        all_jobs = []
        
        # Парсинг hh.ru
        if 'hh.ru' in JOB_SITES:
            all_jobs.extend(self.parse_hh_ru(query))
            # Небольшая задержка между запросами к разным сайтам
            time.sleep(2)
        
        # Парсинг habr.com
        if 'habr.com' in JOB_SITES:
            all_jobs.extend(self.parse_habr_career(query))
            time.sleep(2)
        
        # Здесь можно добавить парсинг других сайтов
        
        return all_jobs
    
    def _apply_filters(self, job):
        """Применение фильтров к вакансии"""
        # Проверка ключевых слов
        if FILTERS['keywords']:
            has_keyword = False
            for keyword in FILTERS['keywords']:
                if (keyword.lower() in job['title'].lower() or 
                    keyword.lower() in job['description'].lower()):
                    has_keyword = True
                    break
            if not has_keyword:
                return False
        
        # Проверка исключающих ключевых слов
        if FILTERS['exclude_keywords']:
            for keyword in FILTERS['exclude_keywords']:
                if (keyword.lower() in job['title'].lower() or 
                    keyword.lower() in job['description'].lower()):
                    return False
        
        # Здесь можно добавить другие фильтры, например, по зарплате
        # Но для этого нужно сначала преобразовать строку с зарплатой в число
        
        return True