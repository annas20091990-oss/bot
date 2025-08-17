import telebot
import sqlite3
import os
import time
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Инициализация бота
try:
    TOKEN = os.environ['TOKEN']
    bot = telebot.TeleBot(TOKEN)
    logger.info("Бот успешно инициализирован")
except KeyError:
    logger.critical("ОШИБКА: Токен не найден в переменных окружения!")
    exit(1)
except Exception as e:
    logger.critical(f"Критическая ошибка при инициализации бота: {str(e)}")
    exit(1)

# Инициализация базы данных
def init_database():
    try:
        logger.info("Инициализация базы данных...")
        conn = sqlite3.connect('users.db', check_same_thread=False)
        cursor = conn.cursor()
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE,
            user_name TEXT,
            firstname TEXT,
            lastname TEXT,
            registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        conn.commit()
        logger.info("База данных успешно инициализирована")
        return conn, cursor
    except sqlite3.Error as e:
        logger.error(f"Ошибка SQLite: {str(e)}")
        logger.critical("Критическая ошибка при инициализации БД. Приложение остановлено.")
        exit(1)
    except Exception as e:
        logger.critical(f"Непредвиденная ошибка при инициализации БД: {str(e)}")
        exit(1)

# Инициализируем БД при старте
conn, cursor = init_database()

@bot.message_handler(commands=['start'])
def start(message):
    try:
        user_id = message.from_user.id
        user_name = message.from_user.username or "N/A"
        firstname = message.from_user.first_name or "N/A"
        lastname = message.from_user.last_name or "N/A"
        
        logger.info(f"Новый запрос /start от {user_id}")
        
        # Проверяем и добавляем пользователя
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        if not cursor.fetchone():
            cursor.execute(
                '''
            INSERT INTO users (user_id, user_name, firstname, lastname)
            VALUES(?, ?, ?, ?)
            ''', (user_id, user_name, firstname, lastname))
            conn.commit()
            logger.info(f"Добавлен новый пользователь: {user_id}")
        
        # Отправка сообщения пользователю
        bot.send_message(
            message.chat.id, 
            '<b>TrendScope - ваш помощник в анализе контента</b>🔍.\n\n'
            '• <b>Мониторит</b> выбранных источников\n'
            '• <b>Оценка</b> <b>динамики</b> просмотров новых публикаций\n'
            '• <b>Контроль</b> показателей через 1, 3, 24 часа и 7 дней\n\n'
            '<b>Получайте уведомления о материалах с высокой динамикой:</b> 💬\n'
            '→ Ссылка и описание публикации\n'
            '→ Показатели вовлеченности\n'
            '→ Ранние метрики просмотров\n\n'
            'Сосредоточьтесь на создании востребованного контента\n'
            'вместо ручного анализа. Наш сервис отслеживает тренды за вас.\n\n'
            'Готовы оптимизировать работу?\n' 
            'Напишите <b>"ДА"</b> для подключения демо-версии.',
            parse_mode='html'
        )

        # Уведомление менеджера
        manager_id = 5661996565
        bot.send_message(
            manager_id, 
            f'🔥 Новый пользователь TrendScope!\n'
            f'ID: {user_id}\n'
            f'Username: @{user_name}\n'
            f'Имя: {firstname} {lastname}'
        )
        logger.info(f"Отправлено уведомление менеджеру о пользователе {user_id}")
        
    except sqlite3.Error as e:
        logger.error(f"Ошибка БД при обработке /start: {str(e)}")
        bot.reply_to(message, "⚠️ Произошла техническая ошибка. Пожалуйста, попробуйте позже.")
    except Exception as e:
        logger.error(f"Ошибка при обработке /start: {str(e)}")
        bot.reply_to(message, "⚠️ Произошла непредвиденная ошибка. Пожалуйста, попробуйте позже.")

@bot.message_handler(func=lambda message: "ДА" in message.text.upper())
def handle_da(message):
    try:
        user_id = message.from_user.id
        logger.info(f"Пользователь {user_id} подтвердил интерес")
        
        bot.send_message(
            message.chat.id, 
            '✅ Отлично! С Вами в ближайшее время свяжется наш менеджер для подключения демо-версии.'
        )
        
        # Уведомление менеджера
        manager_id = 5661996565
        bot.send_message(
            manager_id, 
            f'🚀 Пользователь подтвердил интерес!\n'
            f'ID: {user_id}\n'
            f'Сообщение: "{message.text}"'
        )
        logger.info(f"Отправлено уведомление менеджеру о подтверждении от {user_id}")
        
    except Exception as e:
        logger.error(f"Ошибка при обработке подтверждения: {str(e)}")
        bot.reply_to(message, "⚠️ Произошла ошибка при обработке вашего запроса.")

def run_bot():
    restart_count = 0
    max_restarts = 5
    
    while restart_count < max_restarts:
        try:
            users_count = cursor.execute('SELECT COUNT(*) FROM users').fetchone()[0]
            logger.info(f"Запуск бота | Пользователей в базе: {users_count}")
            logger.info("Бот активен и ожидает сообщений...")
            
            bot.polling(none_stop=True, interval=2, timeout=20)
            
        except sqlite3.Error as e:
            logger.error(f"Ошибка БД: {str(e)}")
            logger.info("Перезапуск бота через 10 секунд...")
            restart_count += 1
            time.sleep(10)
            
        except Exception as e:
            logger.error(f"Общая ошибка: {str(e)}")
            logger.info("Перезапуск бота через 10 секунд...")
            restart_count += 1
            time.sleep(10)
    
    logger.critical(f"Достигнут лимит перезапусков ({max_restarts}). Приложение остановлено.")

if __name__ == '__main__':
    try:
        logger.info("=" * 50)
        logger.info(f"Запуск системы TrendScope Bot")
        logger.info(f"Токен: {'установлен' if os.environ.get('TOKEN') else 'НЕ НАЙДЕН!'}")
        logger.info(f"Версия pyTelegramBotAPI: {telebot.__version__}")
        logger.info("=" * 50)
        
        run_bot()
        
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    finally:
        try:
            if conn:
                conn.close()
                logger.info("Соединение с базой данных закрыто")
        except:
            pass
        logger.info("Работа приложения завершена")
