import telebot
import sqlite3
import os
import time

print("="*50)
print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Запуск бота")
print("="*50)

TOKEN = os.environ['TOKEN']
bot = telebot.TeleBot(TOKEN)

conn = sqlite3.connect('users.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    user_name TEXT,
    firstname TEXT,
    lastname TEXT,
    registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')
conn.commit()

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    user_name = message.from_user.username
    firstname = message.from_user.first_name
    lastname = message.from_user.last_name
    cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id, ))
    if not cursor.fetchone():
        cursor.execute(
            '''
        INSERT INTO users (user_id, user_name, firstname, lastname)
        VALUES(?, ?, ?, ?)
        ''', (user_id, user_name, firstname, lastname))
        conn.commit()
    bot.send_message(
        message.chat.id, 
        '<b>TrendScope - ваш помощник в анализе контента</b>🔍.\n\n'
        '•<b>Мониторит</b> выбранных источников\n'
        '•<b>Оценка</b> <b>динамики</b> просмотров новых публикаций\n'
        '•<b>Контроль</b> показателей через 1, 3, 24 часа и 7 дней\n\n'
        '<b>Получайте уведомления о материалах с высокой динамикой:</b> 💬\n'
        '→ Ссылка и описание публикации \n'
        '→ Показатели вовлеченности\n'
        '→ Ранние метрики просмотров\n\n'
        'Сосредоточьтесь на создании востребованного контента\n'
        'вместо ручного анализа. Наш сервис отслеживает тренды за вас.\n\n'
        'Готовы оптимизировать работу?\n' 
        'Напишите <b>"ДА"</b> для подключения демо-версии.',
        parse_mode='html'
    )

    manager_id = 5661996565
    bot.send_message(
        manager_id, 
        f'Новый пользователь!\nID: {user_id}\nUsername: @{user_name}\nИмя: {firstname} {lastname}'
    )

@bot.message_handler(func=lambda message: "ДА" in message.text.upper())
def handle_da(message):
    bot.send_message(message.chat.id, 'С Вами в ближайшее время свяжется наш менеджер')

def run_bot():
    while True:
        try:
            print(f"[{time.strftime('%H:%M:%S')}] Бот запущен")
            bot.polling(none_stop=True, interval=2, timeout=20)
        except Exception as e:
            print(f"[{time.strftime('%H:%M:%S')}] Ошибка: {str(e)}")
            print("Перезапуск через 10 секунд...")
            time.sleep(10)

if __name__ == '__main__':
    run_bot()