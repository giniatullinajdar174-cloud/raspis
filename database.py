import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Optional

class ScheduleDatabase:
    def __init__(self, db_path: str = "data/schedule.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Инициализация базы данных и создание таблиц"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS classes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS subjects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS schedule (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    class_id INTEGER NOT NULL,
                    day_of_week INTEGER NOT NULL,
                    lesson_number INTEGER NOT NULL,
                    subject_id INTEGER NOT NULL,
                    room TEXT,
                    teacher TEXT,
                    FOREIGN KEY (class_id) REFERENCES classes(id),
                    FOREIGN KEY (subject_id) REFERENCES subjects(id),
                    UNIQUE(class_id, day_of_week, lesson_number)
                )
            """)
            
            conn.commit()
    
    def add_class(self, class_name: str) -> int:
        """Добавление класса"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT OR IGNORE INTO classes (name) VALUES (?)", (class_name,))
            conn.commit()
            cursor.execute("SELECT id FROM classes WHERE name = ?", (class_name,))
            return cursor.fetchone()[0]
    
    def add_subject(self, subject_name: str) -> int:
        """Добавление предмета"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT OR IGNORE INTO subjects (name) VALUES (?)", (subject_name,))
            conn.commit()
            cursor.execute("SELECT id FROM subjects WHERE name = ?", (subject_name,))
            return cursor.fetchone()[0]
    
    def add_lesson(self, class_name: str, day_of_week: int, lesson_number: int, 
                   subject_name: str, room: str = None, teacher: str = None):
        """Добавление урока в расписание"""
        class_id = self.add_class(class_name)
        subject_id = self.add_subject(subject_name)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO schedule 
                (class_id, day_of_week, lesson_number, subject_id, room, teacher)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (class_id, day_of_week, lesson_number, subject_id, room, teacher))
            conn.commit()
    
    def get_schedule_for_day(self, class_name: str, day_of_week: int) -> List[Dict]:
        """Получение расписания для класса на конкретный день"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT s.lesson_number, sub.name as subject, s.room, s.teacher
                FROM schedule s
                JOIN classes c ON s.class_id = c.id
                JOIN subjects sub ON s.subject_id = sub.id
                WHERE c.name = ? AND s.day_of_week = ?
                ORDER BY s.lesson_number
            """, (class_name, day_of_week))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_week_schedule(self, class_name: str) -> Dict[int, List[Dict]]:
        """Получение расписания на всю неделю"""
        week_schedule = {}
        for day in range(1, 8):
            schedule = self.get_schedule_for_day(class_name, day)
            if schedule:
                week_schedule[day] = schedule
        return week_schedule
    
    def get_all_classes(self) -> List[str]:
        """Получение списка всех классов"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM classes ORDER BY name")
            return [row[0] for row in cursor.fetchall()]
    
    def delete_lesson(self, class_name: str, day_of_week: int, lesson_number: int):
        """Удаление урока из расписания"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM schedule 
                WHERE class_id = (SELECT id FROM classes WHERE name = ?)
                AND day_of_week = ? AND lesson_number = ?
            """, (class_name, day_of_week, lesson_number))
            conn.commit()
            return cursor.rowcount > 0
