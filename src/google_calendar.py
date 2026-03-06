from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import datetime
import os
import sys

class GoogleCalendarExporter:
    """
    Класс для экспорта задач в Google Calendar
    """
    
    def __init__(self, credentials_path='credentials/google-credentials.json', calendar_id='primary'):
        """
        Инициализация подключения к Google Calendar
        
        Args:
            credentials_path: путь к JSON-файлу с ключами сервисного аккаунта
            calendar_id: ID календаря ('primary' для основного или конкретный ID)
        """
        self.credentials_path = credentials_path
        self.calendar_id = calendar_id
        self.service = None
        
        # Проверяем наличие файла с ключами
        if not os.path.exists(credentials_path):
            print(f"❌ Файл с ключами не найден: {credentials_path}")
            print("💡 Убедитесь, что файл лежит в папке credentials/")
            sys.exit(1)
        
        self._authenticate()
    
    def _authenticate(self):
        """Аутентификация в Google Calendar API через сервисный аккаунт"""
        try:
            # Определяем права доступа (нужны для записи)
            SCOPES = ['https://www.googleapis.com/auth/calendar']  # Полный доступ к календарю [citation:6]
            
            # Загружаем ключи сервисного аккаунта [citation:5]
            credentials = service_account.Credentials.from_service_account_file(
                self.credentials_path, 
                scopes=SCOPES
            )
            
            # Создаем сервис для работы с Calendar API [citation:6]
            self.service = build('calendar', 'v3', credentials=credentials)
            print("✅ Успешная аутентификация в Google Calendar")
            
        except Exception as e:
            print(f"❌ Ошибка аутентификации: {e}")
            sys.exit(1)
    
    def create_event_from_task(self, task):
        """
        Создает событие в календаре из задачи
        
        Args:
            task: словарь с данными задачи (number, summary, full_description, responsible, due_date, due_date_str)
        
        Returns:
            ссылка на созданное событие или None при ошибке
        """
        if not self.service:
            print("❌ Сервис не инициализирован")
            return None
        
        # Проверяем наличие даты
        if not task.get('due_date'):
            print(f"⚠️ Задача #{task.get('number', '?')} пропущена: нет даты")
            return None
        
        try:
            # Формируем событие
            due_date = task['due_date']
            
            # Создаем событие на целый день (если не указано время) [citation:6]
            # Или можно задать конкретное время, например 10:00
            event_date = due_date.strftime('%Y-%m-%d')
            
            # Берем краткое описание или начало полного
            summary = task.get('summary', '')
            if not summary:
                summary = task.get('full_description', '')[:50] + '...'
            
            # Формируем описание события
            description = f"""
📋 Задача #{task.get('number', '?')}

📝 Полное описание:
{task.get('full_description', '')}

👤 Ответственный: {task.get('responsible', 'Не указан')}

📅 Срок: {task.get('due_date_str', '')}

🔗 Создано автоматически парсером задач
            """.strip()
            
            # Создаем событие [citation:6]
            event = {
                'summary': f"Задача #{task['number']}: {summary}",
                'description': description,
                'start': {
                    'date': event_date,  # Целый день
                },
                'end': {
                    'date': event_date,  # Целый день
                },
                'reminders': {
                    'useDefault': True  # Использовать стандартные напоминания
                }
            }
            
            # Добавляем время, если нужно (например, сделать на 10:00)
            # event['start']['dateTime'] = f"{event_date}T10:00:00+03:00"
            # event['end']['dateTime'] = f"{event_date}T11:00:00+03:00"
            
            # Создаем событие в календаре [citation:1]
            created_event = self.service.events().insert(
                calendarId=self.calendar_id,
                body=event
            ).execute()
            
            print(f"✅ Событие создано: {created_event.get('htmlLink')}")
            return created_event.get('htmlLink')
            
        except HttpError as e:
            print(f"❌ Ошибка API при создании события для задачи #{task.get('number', '?')}: {e}")
            return None
        except Exception as e:
            print(f"❌ Неожиданная ошибка для задачи #{task.get('number', '?')}: {e}")
            return None
    
    def create_events_from_tasks(self, tasks):
        """
        Создает события для списка задач
        
        Args:
            tasks: список словарей с задачами
        
        Returns:
            список ссылок на созданные события
        """
        results = []
        
        print(f"\n📅 Создание событий в календаре (ID: {self.calendar_id})...")
        
        for task in tasks:
            event_link = self.create_event_from_task(task)
            if event_link:
                results.append({
                    'task_number': task.get('number'),
                    'task_summary': task.get('summary', '')[:30] + '...',
                    'event_link': event_link
                })
        
        print(f"\n✅ Создано {len(results)} событий из {len(tasks)} задач")
        return results
    
    def check_calendar_access(self):
        """Проверяет доступ к календарю (выводит список ближайших событий)"""
        try:
            now = datetime.datetime.utcnow().isoformat() + 'Z'
            events_result = self.service.events().list(
                calendarId=self.calendar_id,
                timeMin=now,
                maxResults=5,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            if not events:
                print("📭 В календаре нет предстоящих событий")
            else:
                print(f"📅 Ближайшие события в календаре:")
                for event in events:
                    start = event['start'].get('dateTime', event['start'].get('date'))
                    print(f"   • {start}: {event.get('summary', 'Без названия')}")
            
            return True
            
        except HttpError as e:
            print(f"❌ Ошибка доступа к календарю: {e}")
            print("💡 Проверьте, что:")
            print("   1. Calendar API включен в Google Cloud Console")
            print("   2. Календарь расшарен на email сервисного аккаунта")
            print("   3. Calendar ID указан правильно")
            return False
