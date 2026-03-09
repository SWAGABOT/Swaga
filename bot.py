import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
import sqlite3
import time
from datetime import datetime

# ======================================
# ==== ТВОЙ ТОКЕН ======================
# ======================================
TOKEN = '8451839561:AAE86eHRXSO5G1Tg7DBJSeP7lHbz8q_iLZg'
bot = telebot.TeleBot(TOKEN)

# ======================================
# ==== ТВОЙ ID (АДМИН) =================
# ======================================
ADMIN_ID = 1346528897  # Твой Telegram ID

# ======================================
# ==== БАЗА ДАННЫХ =====================
# ======================================
# Подключаемся к базе данных (создастся автоматически)
conn = sqlite3.connect('users.db', check_same_thread=False)
cursor = conn.cursor()

# Создаем таблицу пользователей если её нет
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id TEXT PRIMARY KEY,
        usdt_balance REAL DEFAULT 0,
        swag_balance REAL DEFAULT 0,
        username TEXT,
        first_seen TEXT
    )
''')
conn.commit()

# ======================================
# ==== ФУНКЦИЯ ДОБАВЛЕНИЯ ПОЛЬЗОВАТЕЛЯ =
# ======================================
def ensure_user_exists(user_id, username=None):
    """Проверяет есть ли пользователь в БД, если нет - добавляет"""
    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    user = cursor.fetchone()
    
    if not user:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute('''
            INSERT INTO users (user_id, usdt_balance, swag_balance, username, first_seen)
            VALUES (?, 0, 0, ?, ?)
        ''', (user_id, username, now))
        conn.commit()
        return True
    return False

# ======================================
# ==== КОМАНДА /START ==================
# ======================================
@bot.message_handler(commands=['start'])
def start(message):
    user_id = str(message.from_user.id)
    username = message.from_user.username or 'NoUsername'
    
    # Добавляем пользователя в базу если его там нет
    ensure_user_exists(user_id, username)
    
    # Создаём кнопку для Web App
    markup = InlineKeyboardMarkup()
    button = InlineKeyboardButton(
        text="🚀 Открыть приложение",
        web_app=WebAppInfo(url="https://swagabot.github.io/Swaga/")
    )
    markup.add(button)
    
    # Отправляем сообщение
    bot.send_message(
        message.chat.id,
        f"👋 Привет, @{username}!\n\nНажми кнопку ниже, чтобы открыть приложение:",
        reply_markup=markup
    )

# ======================================
# ==== КОМАНДА /ID (узнать свой ID) ====
# ======================================
@bot.message_handler(commands=['id'])
def show_id(message):
    bot.reply_to(message, f"🆔 Твой Telegram ID: `{message.from_user.id}`", parse_mode='Markdown')

# ======================================
# ==== КОМАНДА /ADMIN (админ-панель) ===
# ======================================
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    user_id = message.from_user.id
    
    # Проверяем, админ ли это
    if user_id != ADMIN_ID:
        bot.reply_to(message, "❌ У тебя нет доступа к админ-панели")
        return
    
    # Кнопка для открытия админки
    markup = InlineKeyboardMarkup()
    button = InlineKeyboardButton(
        text="👑 Открыть админ-панель",
        web_app=WebAppInfo(url="https://swagabot.github.io/Swaga/admin.html")
    )
    markup.add(button)
    
    bot.send_message(
        user_id,
        "👑 Добро пожаловать в админ-панель\n\n"
        "Нажми кнопку ниже, чтобы открыть статистику и список всех пользователей.",
        reply_markup=markup
    )

# ======================================
# ==== АДМИН КОМАНДЫ (ДЛЯ ТЕСТОВ) ======
# ======================================

@bot.message_handler(commands=['add'])
def admin_add(message):
    """Начислить себе токены: /add 100 usdt  или  /add 500 swag"""
    # Проверяем, что это админ
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "❌ У тебя нет прав администратора")
        return
    
    try:
        parts = message.text.split()
        if len(parts) != 3:
            bot.reply_to(message, "❌ Формат: /add <сумма> <usdt/swag>\nПример: /add 1000 swag")
            return
        
        amount = float(parts[1])
        currency = parts[2].lower()
        
        user_id = str(message.from_user.id)
        
        # Убеждаемся что пользователь есть в БД
        ensure_user_exists(user_id, message.from_user.username)
        
        if currency == 'usdt':
            cursor.execute("UPDATE users SET usdt_balance = usdt_balance + ? WHERE user_id=?", (amount, user_id))
            conn.commit()
            
            # Получаем новый баланс
            cursor.execute("SELECT usdt_balance, swag_balance FROM users WHERE user_id=?", (user_id,))
            new_balance = cursor.fetchone()
            
            bot.reply_to(message, f"✅ Начислено {amount} USDT\n\n💰 Твой баланс:\nUSDT: {new_balance[0]}\nSWAG: {new_balance[1]}")
            
        elif currency == 'swag':
            cursor.execute("UPDATE users SET swag_balance = swag_balance + ? WHERE user_id=?", (amount, user_id))
            conn.commit()
            
            # Получаем новый баланс
            cursor.execute("SELECT usdt_balance, swag_balance FROM users WHERE user_id=?", (user_id,))
            new_balance = cursor.fetchone()
            
            bot.reply_to(message, f"✅ Начислено {amount} SWAG\n\n💰 Твой баланс:\nUSDT: {new_balance[0]}\nSWAG: {new_balance[1]}")
            
        else:
            bot.reply_to(message, "❌ Валюта должна быть usdt или swag")
            
    except ValueError:
        bot.reply_to(message, "❌ Сумма должна быть числом")
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")

@bot.message_handler(commands=['give'])
def admin_give(message):
    """Начислить другому пользователю: /give 123456789 100 swag"""
    # Проверяем, что это админ
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "❌ У тебя нет прав администратора")
        return
    
    try:
        parts = message.text.split()
        if len(parts) != 4:
            bot.reply_to(message, "❌ Формат: /give <user_id> <сумма> <usdt/swag>\nПример: /give 123456789 500 swag")
            return
        
        target_id = parts[1]
        amount = float(parts[2])
        currency = parts[3].lower()
        
        # Убеждаемся что пользователь есть в БД
        ensure_user_exists(target_id)
        
        if currency == 'usdt':
            cursor.execute("UPDATE users SET usdt_balance = usdt_balance + ? WHERE user_id=?", (amount, target_id))
            conn.commit()
            
            # Получаем новый баланс
            cursor.execute("SELECT usdt_balance, swag_balance FROM users WHERE user_id=?", (target_id,))
            new_balance = cursor.fetchone()
            
            bot.reply_to(message, f"✅ Начислено {amount} USDT пользователю {target_id}\n\n💰 Его баланс:\nUSDT: {new_balance[0]}\nSWAG: {new_balance[1]}")
            
        elif currency == 'swag':
            cursor.execute("UPDATE users SET swag_balance = swag_balance + ? WHERE user_id=?", (amount, target_id))
            conn.commit()
            
            # Получаем новый баланс
            cursor.execute("SELECT usdt_balance, swag_balance FROM users WHERE user_id=?", (target_id,))
            new_balance = cursor.fetchone()
            
            bot.reply_to(message, f"✅ Начислено {amount} SWAG пользователю {target_id}\n\n💰 Его баланс:\nUSDT: {new_balance[0]}\nSWAG: {new_balance[1]}")
            
        else:
            bot.reply_to(message, "❌ Валюта должна быть usdt или swag")
            
    except ValueError:
        bot.reply_to(message, "❌ Сумма должна быть числом")
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")

@bot.message_handler(commands=['balance'])
def show_balance(message):
    """Показать свой баланс"""
    user_id = str(message.from_user.id)
    
    # Убеждаемся что пользователь есть в БД
    ensure_user_exists(user_id, message.from_user.username)
    
    cursor.execute("SELECT usdt_balance, swag_balance FROM users WHERE user_id=?", (user_id,))
    balance = cursor.fetchone()
    
    bot.reply_to(message, f"💰 Твой баланс:\nUSDT: {balance[0]}\nSWAG: {balance[1]}")

@bot.message_handler(commands=['balance_user'])
def admin_balance_user(message):
    """Показать баланс другого пользователя (только для админа)"""
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "❌ У тебя нет прав администратора")
        return
    
    try:
        parts = message.text.split()
        if len(parts) != 2:
            bot.reply_to(message, "❌ Формат: /balance_user <user_id>")
            return
        
        target_id = parts[1]
        
        cursor.execute("SELECT usdt_balance, swag_balance, username, first_seen FROM users WHERE user_id=?", (target_id,))
        user = cursor.fetchone()
        
        if user:
            bot.reply_to(message, f"📊 Баланс пользователя {target_id}:\n"
                                  f"👤 Username: @{user[2] if user[2] else 'None'}\n"
                                  f"💰 USDT: {user[0]}\n"
                                  f"💰 SWAG: {user[1]}\n"
                                  f"📅 Зарегистрирован: {user[3]}")
        else:
            bot.reply_to(message, "❌ Пользователь не найден")
            
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")

@bot.message_handler(commands=['users_count'])
def admin_users_count(message):
    """Показать количество пользователей (только для админа)"""
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "❌ У тебя нет прав администратора")
        return
    
    cursor.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()[0]
    
    bot.reply_to(message, f"👥 Всего пользователей в базе: {count}")

@bot.message_handler(commands=['reset'])
def admin_reset(message):
    """Сбросить баланс пользователя (только для админа)"""
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "❌ У тебя нет прав администратора")
        return
    
    try:
        parts = message.text.split()
        if len(parts) != 2:
            bot.reply_to(message, "❌ Формат: /reset <user_id>")
            return
        
        target_id = parts[1]
        
        cursor.execute("UPDATE users SET usdt_balance = 0, swag_balance = 0 WHERE user_id=?", (target_id,))
        conn.commit()
        
        bot.reply_to(message, f"✅ Баланс пользователя {target_id} сброшен")
        
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")

# ======================================
# ==== ЗАПУСК БОТА =====================
# ======================================
if __name__ == "__main__":
    print("✅ Бот запущен")
    print("🌐 Сайт: https://swagabot.github.io/Swaga/")
    print(f"👑 Админ ID: {ADMIN_ID}")
    print("📊 База данных: users.db")
    print("\nДоступные команды:")
    print("  /start - открыть приложение")
    print("  /id - узнать свой Telegram ID")
    print("  /balance - показать свой баланс")
    print("  /admin - открыть админ-панель")
    print("\n🔐 Админ команды (только для тебя):")
    print("  /add <сумма> <usdt/swag> - начислить себе")
    print("  /give <id> <сумма> <usdt/swag> - начислить другому")
    print("  /balance_user <id> - баланс другого")
    print("  /users_count - количество пользователей")
    print("  /reset <id> - сбросить баланс")
    
    # Защита от падений
    while True:
        try:
            bot.polling(none_stop=True, interval=0, timeout=20)
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            time.sleep(5)
            print("🔄 Перезапуск...")
