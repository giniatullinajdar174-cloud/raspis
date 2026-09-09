import sqlite3
import os
from datetime import datetime
3 hidden lines
    def __init__(self, db_path: str = "data/schedule.db"):
        # Отладочная информация
        print(f"DEBUG: Текущая директория: {os.getcwd()}")
        print(f"DEBUG: Ищем базу данных по пути: {db_path}")
        print(f"DEBUG: Файл существует: {os.path.exists(db_path)}")
        if os.path.exists(db_path):
            print(f"DEBUG: Размер файла: {os.path.getsize(db_path)} байт")
        print(f"DEBUG: Файлы в текущей директории: {os.listdir('.')}")
 
        self.db_path = db_path
