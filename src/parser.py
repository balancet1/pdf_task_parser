# src/parser.py
import pdfplumber
import re
from datetime import datetime
from typing import List, Dict, Optional

class TaskParser:
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.tasks = []
        
        # ========== НАСТРОЙКИ ПОЛЕЙ (МЕНЯЙ ЗДЕСЬ!) ==========
        # Ключевые слова для поиска даты (можно добавлять любые)
        self.date_keywords = ['Срок', 'Дата', 'Дедлайн', 'Due', 'Выполнить до', 'Deadline']
        
        # Ключевые слова для поиска ответственного (можно добавлять любые)
        self.resp_keywords = ['Отв.', 'Исполнитель', 'Ответственный', 'Исп.', 'Assignee', 'Responsible']
        
        # Разделители между словом и значением
        self.separators = r'\s*[—–-:]?\s*'  # пробел, тире, двоеточие
        # ====================================================
    
    def extract_text(self) -> str:
        """Извлекает весь текст из PDF"""
        full_text = ""
        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        full_text += text + "\n"
            print(f"✅ Извлечено {len(full_text)} символов из PDF")
            return full_text
        except Exception as e:
            print(f"❌ Ошибка при чтении PDF: {e}")
            return ""
    
    def parse_tasks(self, text: str) -> List[Dict]:
        """Находит задачи в тексте (универсальный парсер)"""
        tasks = []
        
        # Разбиваем текст на строки
        lines = text.split('\n')
        
        current_task = None
        current_description = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Проверяем, начинается ли строка с номера задачи (1., 2., 10., и т.д.)
            task_match = re.match(r'^(\d+)\.\s+(.*)', line)
            
            if task_match:
                # Если уже собирали предыдущую задачу - сохраняем её
                if current_task:
                    self._save_current_task(current_task, current_description)
                    tasks.append(current_task)
                
                # Начинаем новую задачу
                task_num = task_match.group(1)
                task_start = task_match.group(2)
                
                current_task = {
                    'number': int(task_num),
                    'raw_number': task_num,
                    'description_parts': [task_start],
                    'full_description': '',
                    'responsible': '',
                    'due_date': None,
                    'due_date_str': ''
                }
                current_description = [task_start]
            
            elif current_task:
                # Добавляем строку к описанию
                current_description.append(line)
                current_task['description_parts'].append(line)
                
                # ========== ПОИСК ДАТЫ (В ЛЮБОМ МЕСТЕ СТРОКИ) ==========
                # Ищем дату в формате ДД.ММ.ГГГГ после любого ключевого слова
                for keyword in self.date_keywords:
                    escaped_keyword = re.escape(keyword)
                    # Паттерн: ключевое слово + разделитель + дата
                    pattern = rf'{escaped_keyword}{self.separators}(\d{{2}}\.\d{{2}}\.\d{{4}})'
                    date_match = re.search(pattern, line)
                    
                    if date_match:
                        date_str = date_match.group(1).strip()
                        current_task['due_date_str'] = date_str
                        try:
                            current_task['due_date'] = datetime.strptime(date_str, '%d.%m.%Y').date()
                        except ValueError as e:
                            print(f"⚠️ Ошибка парсинга даты {date_str}: {e}")
                        break  # Нашли дату, дальше не ищем
                
                # ========== ПОИСК ОТВЕТСТВЕННОГО (В ЛЮБОМ МЕСТЕ СТРОКИ) ==========
                for keyword in self.resp_keywords:
                    escaped_keyword = re.escape(keyword)
                    
                    # Простой вариант: ищем ключевое слово и всё после до конца строки
                    pattern = rf'{escaped_keyword}{self.separators}([^\n]+)'
                    resp_match = re.search(pattern, line)
                    
                    if resp_match:
                        responsible = resp_match.group(1).strip()
                        
                        # Обрезаем, если дальше идёт ключевое слово даты
                        for date_keyword in self.date_keywords:
                            if date_keyword in responsible:
                                responsible = responsible.split(date_keyword)[0].strip()
                                break
                        
                        # Очищаем от лишних символов
                        responsible = re.sub(r'\s+', ' ', responsible)
                        responsible = re.sub(r'[;,.!?]+$', '', responsible)
                        
                        if responsible:  # Если не пустое
                            current_task['responsible'] = responsible
                            break  # Нашли ответственного, дальше не ищем
        
        # Сохраняем последнюю задачу
        if current_task:
            self._save_current_task(current_task, current_description)
            tasks.append(current_task)
        
        self.tasks = tasks
        return tasks
    
    def _save_current_task(self, task: Dict, description_lines: List[str]):
        """Формирует полное описание задачи"""
        full_desc = ' '.join(description_lines)
        full_desc = re.sub(r'\s+', ' ', full_desc)
        task['full_description'] = full_desc
    
    def print_tasks(self):
        """Выводит найденные задачи в читаемом виде"""
        if not self.tasks:
            print("❌ Задачи не найдены")
            return
        
        print(f"\n📋 Найдено задач: {len(self.tasks)}\n")
        print("=" * 80)
        
        for task in self.tasks:
            print(f"Задача #{task['number']}")
            print(f"📝 Описание: {task['full_description'][:100]}...")
            print(f"👤 Ответственный: {task['responsible'] or '❌ НЕ НАЙДЕН'}")
            print(f"📅 Срок: {task['due_date_str'] or '❌ НЕ НАЙДЕН'}")
            print("-" * 40)
    
    def to_dataframe(self):
        """Конвертирует задачи в pandas DataFrame"""
        import pandas as pd
        
        data = []
        for task in self.tasks:
            data.append({
                '№': task['number'],
                'Описание': task['full_description'],
                'Ответственный': task['responsible'],
                'Срок': task['due_date_str']
            })
        
        df = pd.DataFrame(data)
        return df