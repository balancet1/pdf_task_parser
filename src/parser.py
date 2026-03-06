import pdfplumber
import re
from datetime import datetime
from typing import List, Dict, Optional

class TaskParser:
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.tasks = []
    
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
        """Находит задачи в тексте"""
        tasks = []
        
        # Паттерн для поиска задач:
        # Номер задачи в начале строки (1., 2., и т.д.)
        # Затем описание (может занимать несколько строк)
        # Затем "Отв.:" и "Срок - ДД.ММ.ГГГГ"
        
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
                # Проверяем, содержит ли строка информацию об ответственном и сроке
                if 'Отв.:' in line and 'Срок -' in line:
                    # Парсим ответственнного и дату
                    resp_match = re.search(r'Отв\.:\s*([^С]+)', line)
                    date_match = re.search(r'Срок\s*-\s*(\d{2}\.\d{2}\.\d{4})', line)
                    
                    if resp_match:
                        current_task['responsible'] = resp_match.group(1).strip()
                    if date_match:
                        date_str = date_match.group(1)
                        current_task['due_date_str'] = date_str
                        try:
                            # Парсим дату (формат ДД.ММ.ГГГГ)
                            current_task['due_date'] = datetime.strptime(date_str, '%d.%m.%Y').date()
                        except ValueError as e:
                            print(f"⚠️ Ошибка парсинга даты {date_str}: {e}")
                    
                    # Добавляем эту строку к описанию
                    current_description.append(line)
                    current_task['description_parts'].append(line)
                else:
                    # Продолжение описания задачи
                    current_description.append(line)
                    current_task['description_parts'].append(line)
        
        # Сохраняем последнюю задачу
        if current_task:
            self._save_current_task(current_task, current_description)
            tasks.append(current_task)
        
        self.tasks = tasks
        return tasks
    
    def _save_current_task(self, task: Dict, description_lines: List[str]):
        """Формирует полное описание задачи"""
        task['full_description'] = ' '.join(description_lines)
    
    def print_tasks(self):
        """Выводит найденные задачи в читаемом виде"""
        if not self.tasks:
            print("❌ Задачи не найдены")
            return
        
        print(f"\n📋 Найдено задач: {len(self.tasks)}\n")
        print("=" * 80)
        
        for task in self.tasks:
            print(f"Задача #{task['number']}")
            print(f"Описание: {task['full_description'][:100]}...")  # Первые 100 символов
            print(f"Ответственный: {task['responsible']}")
            print(f"Срок: {task['due_date_str']}")
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
                'Срок': task['due_date_str'],
            })
        
        df = pd.DataFrame(data)
        return df

# Тестирование
if __name__ == "__main__":
    # Путь к PDF файлу
    pdf_file = "data/tasks.pdf"
    
    # Создаем парсер
    parser = TaskParser(pdf_file)
    
    # Извлекаем текст
    text = parser.extract_text()
    
    if text:
        # Парсим задачи
        tasks = parser.parse_tasks(text)
        
        # Выводим результат
        parser.print_tasks()
        
        # Показываем DataFrame
        df = parser.to_dataframe()
        print("\n📊 DataFrame:")
        print(df)