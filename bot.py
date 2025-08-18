import telebot
import sqlite3
import os
import time
import logging
from flask import Flask
import threading
import io
import datetime  # Добавлен импорт datetime

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Создаем минимальный HTTP-сервер для Render.com
app = Flask(__name__)

@app.route('/')
def health_check():
    return "TrendScope Bot is running", 200

def run_flask():
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

print("="*50)
print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Запуск бота TrendScope")
print("="*50)

# Инициализация бота
TOKEN = os.getenv('TOKEN')
if not TOKEN:
    logger.error("Токен не найден! Убедитесь, что переменная TOKEN установлена.")
    exit(1)

bot = telebot.TeleBot(TOKEN)
MANAGER_ID = 5661996565  # ID менеджера для уведомлений

# База данных
def init_db():
    try:
        # Явно указываем путь к файлу БД
        db_path = os.path.join(os.getcwd(), 'users.db')
        conn = sqlite3.connect(db_path, check_same_thread=False)
        cursor = conn.cursor()
        
        # Создаем таблицу
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            demo_requested BOOLEAN DEFAULT 0
        )
        ''')
        conn.commit()
        logger.info("База данных успешно инициализирована")
        return conn, cursor
    except Exception as e:
        logger.error(f"Ошибка инициализации БД: {str(e)}")
        raise

try:
    conn, cursor = init_db()
    logger.info(f"Текущее количество пользователей: {cursor.execute('SELECT COUNT(*) FROM users').fetchone()[0]}")
except Exception as e:
    logger.critical(f"Критическая ошибка при инициализации БД: {str(e)}")
    exit(1)

@bot.message_handler(commands=['start'])
def start(message):
    user = message.from_user
    try:
        # Проверяем существование пользователя
        cursor.execute('SELECT 1 FROM users WHERE user_id = ?', (user.id,))
        exists = cursor.fetchone()
        
        if not exists:
            # Регистрируем нового пользователя
            cursor.execute('''
            INSERT INTO users (user_id, username, first_name, last_name)
            VALUES (?, ?, ?, ?)
            ''', (user.id, user.username, user.first_name, user.last_name))
            conn.commit()
            
            # Уведомляем менеджеру
            bot.send_message(
                MANAGER_ID,
                f"🚀 Новый пользователь TrendScope!\n"
                f"ID: {user.id}\n"
                f"Username: @{user.username}\n"
                f"Имя: {user.first_name} {user.last_name}"
            )
            logger.info(f"Новый пользователь: {user.id}")
        else:
            # Обновляем данные существующего пользователя
            cursor.execute('''
            UPDATE users SET 
                username = ?,
                first_name = ?,
                last_name = ?
            WHERE user_id = ?
            ''', (user.username, user.first_name, user.last_name, user.id))
            conn.commit()

        # Отправляем информационное сообщение
        bot.send_message(
            message.chat.id,
            '<b>TrendScope - ваш помощник в анализе контента</b> 🔍\n\n'
            '• <b>Мониторинг</b> выбранных источников\n'
            '• <b>Оценка динамики</b> просмотров публикаций\n'
            '• <b>Контроль показателей</b> через 1, 3, 24 часа и 7 дней\n\n'
            '<b>Получайте уведомления о трендах:</b>\n'
            '→ Ссылка и описание публикации\n'
            '→ Показатели вовлеченности\n'
            '→ Ранние метрики просмотров\n\n'
            'Сосредоточьтесь на создании контента вместо рутинного анализа.\n\n'
            '<b>Готовы оптимизировать работу?</b>\n'
            'Напишите <b>"ДА"</b> для подключения демо-версии.',
            parse_mode='HTML'
        )

    except Exception as e:
        logger.error(f"Ошибка в /start: {str(e)}")
        bot.send_message(message.chat.id, "⚠️ Произошла техническая ошибка. Попробуйте позже.")

@bot.message_handler(commands=['stats'])
def send_stats(message):
    if message.from_user.id != MANAGER_ID:
        bot.reply_to(message, "⚠️ Доступ запрещен")
        return
        
    try:
        cursor.execute('SELECT COUNT(*) FROM users')
        total_users = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM users WHERE demo_requested=1')
        demo_requests = cursor.fetchone()[0]
        
        response = (
            "📊 Статистика бота:\n"
            f"• Всего пользователей: {total_users}\n"
            f"• Запросов на демо: {demo_requests}"
        )
        
        bot.reply_to(message, response)
        
    except Exception as e:
        logger.error(f"Ошибка в /stats: {str(e)}")
        bot.reply_to(message, "⚠️ Ошибка получения статистики")

@bot.message_handler(commands=['users'])
def send_users_list(message):
    # Проверяем, что команду отправляет менеджер
    if message.from_user.id != MANAGER_ID:
        bot.reply_to(message, "⚠️ Доступ запрещен")
        return
        
    try:
        # Получаем всех пользователей
        cursor.execute('SELECT * FROM users ORDER BY registered_at DESC')
        users = cursor.fetchall()
        
        logger.info(f"Найдено {len(users)} пользователей для выгрузки")
        
        if not users:
            bot.reply_to(message, "В базе данных пока нет пользователей")
            return
            
        # Создаем текстовый файл с данными
        file_content = "Список пользователей TrendScope:\n\n"
        file_content += "ID пользователя | Username | Имя | Фамилия | Дата регистрации | Демо запрошено\n"
        file_content += "-------------------------------------------------------------------------------\n"
        
        for user in users:
            user_id = user[0]
            username = f"@{user[1]}" if user[1] else "нет"
            first_name = user[2] or "нет"
            last_name = user[3] or "нет"
            
            # Форматируем дату регистрации
            reg_date = user[4]
            if reg_date:
                # Если дата в строковом формате
                if isinstance(reg_date, str):
                    # Убираем миллисекунды если есть
                    reg_date = reg_date.split('.')[0]
                formatted_date = str(reg_date)
            else:
                formatted_date = "неизвестно"
            
            demo_requested = "✅" if user[5] else "❌"
            
            file_content += f"{user_id} | {username} | {first_name} | {last_name} | {formatted_date} | {demo_requested}\n"
        
        # Создаем файл в памяти
        file_in_memory = io.BytesIO(file_content.encode('utf-8'))
        file_in_memory.seek(0)  # КРИТИЧЕСКИ ВАЖНО: перемещаем указатель в начало
        file_in_memory.name = 'users_list.txt'
        
        # Отправляем файл
        bot.send_document(
            message.chat.id,
            file_in_memory,
            caption="📋 Полный список пользователей"
        )
        
        logger.info(f"Успешно отправлен список из {len(users)} пользователей")
        
    except Exception as e:
        logger.error(f"Ошибка в /users: {str(e)}", exc_info=True)
        bot.reply_to(message, f"⚠️ Ошибка при получении списка пользователей: {str(e)}")

@bot.message_handler(func=lambda m: m.text and m.text.upper().strip() == "ДА")
def handle_demo_request(message):
    try:
        user = message.from_user
        
        # Проверяем регистрацию пользователя
        cursor.execute('SELECT 1 FROM users WHERE user_id = ?', (user.id,))
        if not cursor.fetchone():
            bot.send_message(
                message.chat.id,
                "ℹ️ Пожалуйста, сначала зарегистрируйтесь с помощью /start"
            )
            return

        # Проверяем предыдущие запросы
        cursor.execute(
            'SELECT demo_requested FROM users WHERE user_id = ?', 
            (user.id,)
        )
        demo_requested = cursor.fetchone()[0]
        
        if not demo_requested:
            # Обновляем статус демо
            cursor.execute('''
            UPDATE users SET demo_requested = 1
            WHERE user_id = ?
            ''', (user.id,))
            conn.commit()
            
            # Уведомляем менеджеру о запросе демо
            bot.send_message(
                MANAGER_ID,
                f"🔥 Запрос на демо-версию!\n"
                f"Пользователь: @{user.username}\n"
                f"ID: {user.id}\n"
                f"Имя: {user.first_name} {user.last_name}"
            )
            logger.info(f"Запрос демо от: {user.id}")

        bot.send_message(
            message.chat.id,
            "✅ Спасибо за интерес! Наш менеджер свяжется с вами в ближайшее время "
            "для подключения демо-версии."
        )

    except Exception as e:
        logger.error(f"Ошибка обработки ДА: {str(e)}")
        bot.send_message(message.chat.id, "⚠️ Произошла ошибка при обработке запроса.")

def run_bot():
    logger.info("Бот запущен")
    while True:
        try:
            user_count = cursor.execute('SELECT COUNT(*) FROM users').fetchone()[0]
            logger.info(f"Статус: Активен | Пользователей: {user_count}")
            
            # Удаляем вебхук перед запуском
            bot.remove_webhook()
            time.sleep(1)
            
            # Запускаем long polling
            bot.polling(none_stop=True, interval=3, timeout=25)
            
        except Exception as e:
            logger.error(f"Ошибка: {str(e)}")
            logger.info("Перезапуск через 30 секунд...")
            time.sleep(30)

if __name__ == '__main__':
    logger.info(f"Токен: {'установлен' if TOKEN else 'НЕ НАЙДЕН!'}")
    
    # Запускаем HTTP-сервер в отдельном потоке
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    
    run_bot()
