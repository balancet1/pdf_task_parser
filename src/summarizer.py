import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import re
from typing import Optional

class TaskSummarizer:
    def __init__(self, model_name="cointegrated/rut5-base-absum"):
        """
        Инициализация модели для суммаризации
        """
        self.model_name = model_name
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.tokenizer = None
        self.model = None
        
        print(f"🔄 Загрузка модели {model_name}...")
        print(f"📱 Устройство: {self.device}")
        
        try:
            # Загружаем токенизатор и модель
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
            self.model.to(self.device)
            self.model.eval()  # Режим оценки (не обучения)
            print("✅ Модель успешно загружена!")
        except Exception as e:
            print(f"❌ Ошибка при загрузке модели: {e}")
            print("💡 Попробуйте выполнить: pip install --upgrade transformers torch")
            raise
    
    def summarize(self, text: str, max_length: int = 50, min_length: int = 10) -> str:
        """
        Создает краткую суммаризацию текста задачи
        
        Args:
            text: Полный текст задачи
            max_length: Максимальная длина суммаризации
            min_length: Минимальная длина суммаризации
            
        Returns:
            Краткое описание задачи
        """
        if not text or len(text) < 20:
            return text
        
        try:
            # Очищаем текст от лишних символов
            text = self._clean_text(text)
            
            # Токенизируем входной текст
            inputs = self.tokenizer(
                text, 
                max_length=512, 
                truncation=True, 
                return_tensors="pt"
            ).to(self.device)
            
            # Генерируем суммаризацию
            with torch.no_grad():  # Отключаем вычисление градиентов для экономии памяти
                summary_ids = self.model.generate(
                    inputs.input_ids,
                    max_length=max_length,
                    min_length=min_length,
                    num_beams=4,  # Поиск с лучом для лучшего качества
                    length_penalty=2.0,  # Штраф за длину
                    early_stopping=True,
                    no_repeat_ngram_size=3  # Избегаем повторений
                )
            
            # Декодируем результат
            summary = self.tokenizer.decode(summary_ids[0], skip_special_tokens=True)
            
            # Постобработка
            summary = self._postprocess_summary(summary)
            
            return summary
            
        except Exception as e:
            print(f"⚠️ Ошибка при суммаризации: {e}")
            # Возвращаем первые 100 символов как запасной вариант
            return text[:100] + "..."
    
    def _clean_text(self, text: str) -> str:
        """Очищает текст от лишних символов"""
        # Удаляем номер задачи в начале (если есть)
        text = re.sub(r'^\d+\.\s*', '', text)
        
        # Удаляем информацию об ответственном и сроке
        text = re.sub(r'Отв\.:.*?Срок\s*-\s*\d{2}\.\d{2}\.\d{4}', '', text)
        text = re.sub(r'Отв\.:.*$', '', text, flags=re.MULTILINE)
        text = re.sub(r'Срок\s*-\s*\d{2}\.\d{2}\.\d{4}', '', text)
        
        # Удаляем лишние пробелы
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def _postprocess_summary(self, summary: str) -> str:
        """Постобработка сгенерированной суммаризации"""
        # Убираем лишние пробелы
        summary = re.sub(r'\s+', ' ', summary)
        
        # Убираем точку в конце, если её нет
        if summary and not summary.endswith(('.', '!', '?')):
            summary += '.'
        
        # Делаем первую букву заглавной
        if summary:
            summary = summary[0].upper() + summary[1:]
        
        return summary
    
    def summarize_batch(self, texts, max_length=50, min_length=10):
        """
        Суммаризация нескольких текстов (для эффективности)
        """
        summaries = []
        for text in texts:
            summary = self.summarize(text, max_length, min_length)
            summaries.append(summary)
        return summaries

