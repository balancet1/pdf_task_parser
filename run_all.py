# ОБРАБОТКА ВСЕХ PDF-файлов в папке /data

import os
import glob
from src.main_with_calendar import TaskProcessor

def process_all_pdfs():
    # Настройки (вставь свои данные)
    calendar_id = "nikolaevsub@gmail.com"  # твой ID календаря  
    sheets_url = "https://docs.google.com/spreadsheets/d/.../edit"  # твоя ссылка
    
    # Найти все PDF файлы в папке data
    pdf_files = glob.glob("data/*.pdf")
    
    if not pdf_files:
        print("❌ В папке data/ нет PDF файлов")
        return
    
    print(f"📁 Найдено PDF файлов: {len(pdf_files)}")
    print("=" * 60)
    
    # Создаём общую таблицу для результатов
    all_results = []
    
    for i, pdf_file in enumerate(pdf_files, 1):
        print(f"\n📄 Файл {i}/{len(pdf_files)}: {os.path.basename(pdf_file)}")
        print("-" * 40)
        
        # Обработать каждый файл
        processor = TaskProcessor(pdf_file, use_summarizer=True)
        
        if processor.process():
            # Сохраняем в отдельный Excel файл
            excel_name = f"output/tasks_{i}_{os.path.basename(pdf_file).replace('.pdf', '')}.xlsx"
            processor.save_to_excel(excel_name)
            
            # Добавляем в общий список для сводки
            all_results.append({
                'file': os.path.basename(pdf_file),
                'count': len(processor.tasks)
            })
            
            # Экспорт в Google (опционально)
            if sheets_url:
                processor.save_to_google_sheets(sheets_url, sheet_name=f"Файл_{i}")
            if calendar_id:
                processor.save_to_google_calendar(calendar_id)
        else:
            print(f"⚠️ Ошибка обработки {pdf_file}")
    
    # Итоговая статистика
    print("\n" + "=" * 60)
    print("📊 ИТОГОВАЯ СТАТИСТИКА")
    print("=" * 60)
    total = 0
    for r in all_results:
        print(f"📄 {r['file']}: {r['count']} задач")
        total += r['count']
    print(f"\n✅ Всего обработано файлов: {len(all_results)}")
    print(f"✅ Всего найдено задач: {total}")

if __name__ == "__main__":
    process_all_pdfs()