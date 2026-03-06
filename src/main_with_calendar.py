import os
import sys
import argparse
from pathlib import Path

# Добавляем путь к src для импортов
sys.path.append(str(Path(__file__).parent))

from parser import TaskParser
from summarizer import TaskSummarizer
from excel_exporter import ExcelExporter
from google_sheets import GoogleSheetsExporter
from google_calendar import GoogleCalendarExporter
import pandas as pd
from datetime import datetime

class TaskProcessor:
    def __init__(self, pdf_path: str, use_summarizer: bool = True):
        """
        Основной класс для обработки задач
        """
        self.pdf_path = pdf_path
        self.use_summarizer = use_summarizer
        self.tasks = []
        self.df = None
        
        # Инициализируем компоненты
        self.parser = TaskParser(pdf_path)
        
        if use_summarizer:
            try:
                print("🤖 Загрузка суммаризатора...")
                self.summarizer = TaskSummarizer()
            except Exception as e:
                print(f"⚠️ Ошибка загрузки суммаризатора: {e}")
                self.use_summarizer = False
    
    def process(self):
        """
        Основной метод обработки
        """
        print(f"\n📄 Чтение файла: {self.pdf_path}")
        
        # Извлекаем текст
        text = self.parser.extract_text()
        if not text:
            print("❌ Не удалось извлечь текст")
            return False
        
        # Парсим задачи
        print("🔍 Поиск задач...")
        self.tasks = self.parser.parse_tasks(text)
        
        if not self.tasks:
            print("❌ Задачи не найдены")
            return False
        
        print(f"✅ Найдено задач: {len(self.tasks)}")
        
        # Суммаризация
        if self.use_summarizer:
            print("🔄 Генерация кратких описаний...")
            for task in self.tasks:
                task['summary'] = self.summarizer.summarize(task['full_description'])
        else:
            for task in self.tasks:
                task['summary'] = task['full_description'][:100] + "..."
        
        # Создаем DataFrame
        self.df = self._create_dataframe()
        
        return True
    
    def _create_dataframe(self):
        """
        Создает DataFrame из задач
        """
        data = []
        for task in self.tasks:
            data.append({
                '№': task['number'],
                'Краткое описание': task.get('summary', ''),
                'Описание': task['full_description'],
                'Ответственный': task['responsible'],
                'Срок': task['due_date_str']
            })
        return pd.DataFrame(data)
    
    def save_to_excel(self, filename="output/tasks.xlsx"):
        """Сохраняет задачи в Excel"""
        if self.df is None:
            print("❌ Нет данных для сохранения")
            return
        
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        exporter = ExcelExporter(self.df)
        exporter.export(filename)
        print(f"💾 Excel файл сохранен: {filename}")
    
    def save_to_google_sheets(self, spreadsheet_url, sheet_name="Задачи"):
        """
        Сохраняет задачи в существующую Google таблицу
        """
        if self.df is None:
            print("❌ Нет данных для сохранения")
            return False
        
        print("\n☁️ Экспорт в Google Sheets...")
        
        sheets_exporter = GoogleSheetsExporter()
        
        if sheets_exporter.use_existing_spreadsheet(spreadsheet_url):
            sheets_exporter.export_dataframe(self.df, sheet_name=sheet_name)
            print(f"✅ Данные записаны в таблицу")
            print(f"🔗 {spreadsheet_url}")
            return True
        else:
            print("❌ Экспорт в Google Sheets не удался")
            return False
    
    def save_to_google_calendar(self, calendar_id='primary'):
        """
        Создает события в Google Calendar из задач с датами
        
        Args:
            calendar_id: ID календаря (по умолчанию 'primary')
        """
        if not self.tasks:
            print("❌ Нет задач для экспорта")
            return False
        
        print("\n📅 Экспорт в Google Calendar...")
        
        calendar = GoogleCalendarExporter(calendar_id=calendar_id)
        
        # Проверяем доступ
        if not calendar.check_calendar_access():
            return False
        
        # Создаем события
        results = calendar.create_events_from_tasks(self.tasks)
        
        # Статистика
        tasks_with_dates = sum(1 for t in self.tasks if t.get('due_date'))
        print(f"\n📊 Статистика по календарю:")
        print(f"   Всего задач: {len(self.tasks)}")
        print(f"   Задач с датами: {tasks_with_dates}")
        print(f"   Создано событий: {len(results)}")
        
        return len(results) > 0
    
    def print_summary(self):
        """Выводит краткую сводку"""
        if not self.tasks:
            return
        
        print("\n" + "="*60)
        print("📊 ИТОГОВЫЙ ОТЧЕТ")
        print("="*60)
        
        # Статистика
        print(f"\n📈 Статистика:")
        print(f"   Всего задач: {len(self.tasks)}")
        
        # По ответственным
        responsible_counts = {}
        for task in self.tasks:
            resp = task['responsible'] or 'Не назначен'
            responsible_counts[resp] = responsible_counts.get(resp, 0) + 1
        
        print("\n👥 Задачи по ответственным:")
        for resp, count in sorted(responsible_counts.items()):
            print(f"   {resp}: {count}")
        
        # По наличию дат
        tasks_with_dates = sum(1 for t in self.tasks if t.get('due_date'))
        print(f"\n📅 Задачи с датами: {tasks_with_dates} из {len(self.tasks)}")


def main():
    """
    Основная функция программы
    """
    parser = argparse.ArgumentParser(description='Парсер задач из PDF с экспортом в Excel, Google Sheets и Calendar')
    parser.add_argument('pdf_file', nargs='?', default='data/tasks.pdf',
                       help='Путь к PDF файлу')
    parser.add_argument('--no-summary', action='store_true',
                       help='Отключить суммаризацию')
    parser.add_argument('--excel', '-e', default='output/tasks.xlsx',
                       help='Имя выходного файла Excel')
    parser.add_argument('--sheets', '-s', metavar='URL',
                       help='URL Google таблицы для экспорта')
    parser.add_argument('--calendar', '-c', metavar='ID',
                       nargs='?', const='primary', default=None,
                       help='ID календаря для экспорта (по умолчанию primary)')
    
    args = parser.parse_args()
    
    print("="*60)
    print("🚀 ПАРСЕР ЗАДАЧ ИЗ PDF")
    print("="*60)
    
    # Проверяем существование файла
    if not os.path.exists(args.pdf_file):
        print(f"❌ Файл не найден: {args.pdf_file}")
        return
    
    # Создаем обработчик
    processor = TaskProcessor(args.pdf_file, use_summarizer=not args.no_summary)
    
    # Обрабатываем
    if processor.process():
        # Выводим сводку
        processor.print_summary()
        
        # Сохраняем в Excel (всегда)
        processor.save_to_excel(args.excel)
        
        # Сохраняем в Google Sheets, если указан URL
        if args.sheets:
            processor.save_to_google_sheets(args.sheets)
        
        # Сохраняем в Google Calendar, если указан
        if args.calendar is not None:
            processor.save_to_google_calendar(calendar_id=args.calendar)
        
        print(f"\n✨ Готово! Результаты сохранены локально в {args.excel}")
    else:
        print("❌ Обработка не удалась")

if __name__ == "__main__":
    main()