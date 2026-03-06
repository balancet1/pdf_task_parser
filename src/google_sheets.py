import gspread
from google.oauth2.service_account import Credentials
from google.auth.exceptions import GoogleAuthError
import pandas as pd
from datetime import datetime
import os
import sys

class GoogleSheetsExporter:
    """
    Класс для экспорта задач в Google Sheets (исправленная версия)
    """
    
    def __init__(self, credentials_path='credentials/google-credentials.json'):
        """
        Инициализация подключения к Google Sheets
        """
        self.credentials_path = credentials_path
        self.client = None
        self.spreadsheet = None
        
        # Проверяем наличие файла с ключами
        if not os.path.exists(credentials_path):
            print(f"❌ Файл с ключами не найден: {credentials_path}")
            print("💡 Убедитесь, что файл лежит в папке credentials/")
            sys.exit(1)
        
        self._authenticate()
    
    def _authenticate(self):
        """Аутентификация в Google Sheets API"""
        try:
            # Определяем права доступа
            scope = [
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive'
            ]
            
            # Загружаем ключи
            credentials = Credentials.from_service_account_file(
                self.credentials_path, 
                scopes=scope
            )
            
            # Авторизуемся
            self.client = gspread.authorize(credentials)
            print("✅ Успешная аутентификация в Google Sheets")
            
        except Exception as e:
            print(f"❌ Ошибка аутентификации: {e}")
            sys.exit(1)
    
    def use_existing_spreadsheet(self, spreadsheet_identifier):
        """
        ИСПРАВЛЕНО: Открывает существующую таблицу (по URL, ID или названию)
        
        Args:
            spreadsheet_identifier: URL, ID или название таблицы
        """
        try:
            # Пробуем открыть по URL
            if spreadsheet_identifier.startswith('https://'):
                self.spreadsheet = self.client.open_by_url(spreadsheet_identifier)
                print(f"✅ Открыта таблица по URL")
            else:
                # Пробуем открыть по ID или названию
                try:
                    self.spreadsheet = self.client.open_by_key(spreadsheet_identifier)
                except:
                    self.spreadsheet = self.client.open(spreadsheet_identifier)
            
            print(f"✅ Таблица: {self.spreadsheet.title}")
            return self.spreadsheet
            
        except gspread.SpreadsheetNotFound:
            print(f"❌ Таблица не найдена. Проверьте:")
            print(f"   1. Правильно ли вы скопировали ссылку/ID")
            print(f"   2. Расшарили ли таблицу на email сервисного аккаунта")
            return None
        except Exception as e:
            print(f"❌ Ошибка при открытии таблицы: {e}")
            return None
    
    def export_dataframe(self, df, sheet_name='Tasks', clear_sheet=True):
        """
        Экспортирует DataFrame в открытую Google таблицу
        """
        if self.spreadsheet is None:
            print("❌ Сначала откройте таблицу через use_existing_spreadsheet()")
            return False
        
        try:
            # Проверяем, существует ли лист с таким названием
            try:
                worksheet = self.spreadsheet.worksheet(sheet_name)
                if clear_sheet:
                    worksheet.clear()
                    print(f"🧹 Лист '{sheet_name}' очищен")
            except gspread.WorksheetNotFound:
                # Создаем новый лист
                worksheet = self.spreadsheet.add_worksheet(
                    title=sheet_name,
                    rows=max(100, len(df) + 10),
                    cols=len(df.columns) + 5
                )
                print(f"📄 Создан новый лист: '{sheet_name}'")
            
            # Подготавливаем данные
            headers = df.columns.tolist()
            data = df.values.tolist()
            all_data = [headers] + data
            
            # Записываем
            worksheet.update('A1', all_data)
            print(f"✅ Записано {len(df)} строк в лист '{sheet_name}'")
            
            return worksheet
            
        except Exception as e:
            print(f"❌ Ошибка при экспорте: {e}")
            return False
    
    def get_shareable_link(self):
        """Возвращает ссылку на таблицу"""
        if self.spreadsheet:
            return self.spreadsheet.url
        return None