import telebot
import sqlite3
import os
import time
import logging

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

print("="*50)
print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Запуск бота TrendScope")
print("="*50)

# Инициализация бота
TOKEN = os.getenv('TOKEN')
if not TOKEN:
    logger.error("Токен не найден! Убедитесь, что переменная TOKEN установлена.")
    exit(1)

bot = telebot.TeleBot(TOKEN)
MANAGER_ID = 5661996565

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
            
            # Уведомляем менеджера
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
            
            # Уведомляем менеджера о запросе демо
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
            logger.info(f"Статус: Активен | Пользователей: {cursor.execute('SELECT COUNT(*) FROM users').fetchone()[0]}")
            bot.infinity_polling()
        except Exception as e:
            logger.error(f"Ошибка: {str(e)}")
            logger.info("Перезапуск через 10 секунд...")
            time.sleep(10)

if __name__ == '__main__':
    logger.info(f"Токен: {'установлен' if TOKEN else 'НЕ НАЙДЕН!'}")
    run_bot()
