import os
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
from database import ScheduleDatabase

# Загрузка переменных окружения
load_dotenv()

# Инициализация базы данных
db = ScheduleDatabase("data/schedule.db")

# Дни недели
DAYS_OF_WEEK = {
    1: "Понедельник",
    2: "Вторник", 
    3: "Среда",
    4: "Четверг",
    5: "Пятница",
    6: "Суббота",
    7: "Воскресенье"
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start с главным меню"""
    welcome_message = """
👋 Привет! Я бот для просмотра расписания уроков.

Выберите действие в меню ниже:
    """
    
    # Создаем главное меню с кнопками
    keyboard = [
        [InlineKeyboardButton("📅 Сегодня", callback_data="today")],
        [InlineKeyboardButton("📅 Завтра", callback_data="tomorrow")],
        [InlineKeyboardButton("📚 На неделю", callback_data="week")],
        [InlineKeyboardButton("🏫 Список классов", callback_data="classes")],
        [InlineKeyboardButton("❓ Справка", callback_data="help")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(welcome_message, reply_markup=reply_markup)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /help"""
    await help_button(update)

async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /menu - показать главное меню"""
    await show_main_menu(update)

async def show_classes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать список классов"""
    classes = db.get_all_classes()
    
    if not classes:
        await update.message.reply_text("❌ В базе данных нет классов.")
        return
    
    # Создаем клавиатуру с классами
    keyboard = []
    for class_name in classes:
        keyboard.append([InlineKeyboardButton(class_name, callback_data=f"class_{class_name}")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🏫 Выберите класс:", reply_markup=reply_markup)

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка нажатий на кнопки"""
    query = update.callback_query
    await query.answer()
    
    # Главное меню
    if query.data == "today":
        await today_schedule_button(query)
    elif query.data == "tomorrow":
        await tomorrow_schedule_button(query)
    elif query.data == "week":
        await week_schedule_button(query)
    elif query.data == "classes":
        await show_classes_button(query)
    elif query.data == "help":
        await help_button(query)
    elif query.data == "back_to_classes":
        await show_classes_button(query)
    elif query.data == "back_to_menu":
        await show_main_menu(query)
    # Выбор класса
    elif query.data.startswith("class_"):
        class_name = query.data.replace("class_", "")
        await show_class_menu(query, class_name)
    # Выбор дня недели
    elif query.data.startswith("day_"):
        parts = query.data.split("_")
        class_name = parts[2]
        day_of_week = int(parts[1])
        await show_day_schedule(query, class_name, day_of_week)
    # Расписание на неделю для класса
    elif query.data.startswith("week_"):
        class_name = query.data.replace("week_", "")
        await show_week_schedule_text(query, class_name)

async def show_class_menu(update, class_name: str):
    """Показать меню для выбранного класса"""
    keyboard = []
    
    # Кнопки для каждого дня недели
    for day_num, day_name in DAYS_OF_WEEK.items():
        if day_num <= 6:  # Только будние дни
            keyboard.append([InlineKeyboardButton(day_name, callback_data=f"day_{day_num}_{class_name}")])
    
    # Кнопка для всего расписания
    keyboard.append([InlineKeyboardButton("📅 Вся неделя", callback_data=f"week_{class_name}")])
    keyboard.append([InlineKeyboardButton("◀️ Назад к классам", callback_data="back_to_classes")])
    keyboard.append([InlineKeyboardButton("🏠 Главное меню", callback_data="back_to_menu")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(f"📚 Класс {class_name}. Выберите день:", reply_markup=reply_markup)

async def show_day_schedule(update, class_name: str, day_of_week: int):
    """Показать расписание на конкретный день"""
    schedule = db.get_schedule_for_day(class_name, day_of_week)
    day_name = DAYS_OF_WEEK.get(day_of_week, "Неизвестный день")
    
    if not schedule:
        keyboard = [
            [InlineKeyboardButton("◀️ Назад к классу", callback_data=f"class_{class_name}")],
            [InlineKeyboardButton("🏠 Главное меню", callback_data="back_to_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(f"❌ Нет расписания на {day_name} для класса {class_name}", reply_markup=reply_markup)
        return
    
    message = f"📅 {day_name} - Класс {class_name}\n\n"
    
    for lesson in schedule:
        lesson_num = lesson['lesson_number']
        subject = lesson['subject']
        room = lesson.get('room', 'Не указано')
        teacher = lesson.get('teacher', 'Не указано')
        
        message += f"🔹 Урок {lesson_num}: {subject}\n"
        message += f"   📍 Кабинет: {room}\n"
        message += f"   👨‍🏫 Учитель: {teacher}\n\n"
    
    keyboard = [
        [InlineKeyboardButton("◀️ Назад к классу", callback_data=f"class_{class_name}")],
        [InlineKeyboardButton("🏠 Главное меню", callback_data="back_to_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(message, reply_markup=reply_markup)

async def today_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Расписание на сегодня"""
    today = datetime.now().weekday() + 1  # 1-7 (Понедельник-Воскресенье)
    
    if today > 6:  # Воскресенье
        await update.message.reply_text("😴 Сегодня воскресенье, уроков нет!")
        return
    
    # Показываем список классов для выбора
    await show_classes(update, context)
    await update.message.reply_text(f"📅 Сегодня {DAYS_OF_WEEK[today]}. Выберите класс:")

async def tomorrow_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Расписание на завтра"""
    tomorrow = (datetime.now().weekday() + 2) % 7
    if tomorrow == 0:
        tomorrow = 7
    
    if tomorrow > 6:  # Воскресенье
        await update.message.reply_text("😴 Завтра воскресенье, уроков нет!")
        return
    
    # Показываем список классов для выбора
    await show_classes(update, context)
    await update.message.reply_text(f"📅 Завтра {DAYS_OF_WEEK[tomorrow]}. Выберите класс:")

async def week_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Расписание на неделю"""
    # Проверяем, указан ли класс
    if context.args:
        class_name = context.args[0]
        await show_week_schedule_text(update, class_name)
    else:
        await show_classes(update, context)
        await update.message.reply_text("📅 Выберите класс для просмотра расписания на неделю:")

async def show_week_schedule_text(update, class_name: str):
    """Показать расписание на неделю текстом"""
    week_schedule = db.get_week_schedule(class_name)
    
    if not week_schedule:
        await update.message.reply_text(f"❌ Нет расписания для класса {class_name}")
        return
    
    message = f"📚 Расписание класса {class_name} на неделю:\n\n"
    
    for day_num, lessons in sorted(week_schedule.items()):
        day_name = DAYS_OF_WEEK.get(day_num, "Неизвестный день")
        message += f"📅 {day_name}:\n"
        
        for lesson in lessons:
            lesson_num = lesson['lesson_number']
            subject = lesson['subject']
            room = lesson.get('room', '?')
            message += f"   {lesson_num}. {subject} (каб. {room})\n"
        
        message += "\n"
    
    keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data=f"class_{class_name}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(message, reply_markup=reply_markup)

async def show_main_menu(update):
    """Показать главное меню"""
    welcome_message = """
👋 Главное меню

Выберите действие:
    """
    
    keyboard = [
        [InlineKeyboardButton("📅 Сегодня", callback_data="today")],
        [InlineKeyboardButton("📅 Завтра", callback_data="tomorrow")],
        [InlineKeyboardButton("📚 На неделю", callback_data="week")],
        [InlineKeyboardButton("🏫 Список классов", callback_data="classes")],
        [InlineKeyboardButton("❓ Справка", callback_data="help")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(welcome_message, reply_markup=reply_markup)

async def show_classes_button(update):
    """Показать список классов через кнопку"""
    classes = db.get_all_classes()
    
    if not classes:
        await update.message.reply_text("❌ В базе данных нет классов.")
        return
    
    # Создаем клавиатуру с классами
    keyboard = []
    for class_name in classes:
        keyboard.append([InlineKeyboardButton(class_name, callback_data=f"class_{class_name}")])
    
    # Добавляем кнопку возврата в главное меню
    keyboard.append([InlineKeyboardButton("◀️ Главное меню", callback_data="back_to_menu")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🏫 Выберите класс:", reply_markup=reply_markup)

async def today_schedule_button(update):
    """Расписание на сегодня через кнопку"""
    today = datetime.now().weekday() + 1  # 1-7 (Понедельник-Воскресенье)
    
    if today > 6:  # Воскресенье
        keyboard = [[InlineKeyboardButton("◀️ Главное меню", callback_data="back_to_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("😴 Сегодня воскресенье, уроков нет!", reply_markup=reply_markup)
        return
    
    # Показываем список классов для выбора
    await show_classes_button(update)
    await update.message.reply_text(f"📅 Сегодня {DAYS_OF_WEEK[today]}. Выберите класс:")

async def tomorrow_schedule_button(update):
    """Расписание на завтра через кнопку"""
    tomorrow = (datetime.now().weekday() + 2) % 7
    if tomorrow == 0:
        tomorrow = 7
    
    if tomorrow > 6:  # Воскресенье
        keyboard = [[InlineKeyboardButton("◀️ Главное меню", callback_data="back_to_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("😴 Завтра воскресенье, уроков нет!", reply_markup=reply_markup)
        return
    
    # Показываем список классов для выбора
    await show_classes_button(update)
    await update.message.reply_text(f"📅 Завтра {DAYS_OF_WEEK[tomorrow]}. Выберите класс:")

async def week_schedule_button(update):
    """Расписание на неделю через кнопку"""
    await show_classes_button(update)
    await update.message.reply_text("📅 Выберите класс для просмотра расписания на неделю:")

async def help_button(update):
    """Справка через кнопку"""
    help_text = """
📖 Справка:

📅 Функции бота:
• Сегодня - расписание на текущий день
• Завтра - расписание на следующий день
• На неделю - полное расписание на неделю
• Список классов - все доступные классы

💡 Как пользоваться:
1. Выберите нужную функцию в меню
2. Выберите свой класс
3. Просмотрите расписание
    """
    
    keyboard = [[InlineKeyboardButton("◀️ Главное меню", callback_data="back_to_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(help_text, reply_markup=reply_markup)

def main():
    """Запуск бота"""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    
    if not token:
        print("Error: TELEGRAM_BOT_TOKEN not found in .env file")
        return
    
    # Создание приложения
    application = Application.builder().token(token).build()
    
    # Регистрация обработчиков команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("menu", menu_command))
    application.add_handler(CommandHandler("classes", show_classes))
    application.add_handler(CommandHandler("today", today_schedule))
    application.add_handler(CommandHandler("tomorrow", tomorrow_schedule))
    application.add_handler(CommandHandler("week", week_schedule))
    
    # Регистрация обработчика кнопок
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # Запуск бота
    print("Bot started...")
    application.run_polling()

if __name__ == "__main__":
    main()
