import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

# ======================================
# ==== ТВОЙ НОВЫЙ ТОКЕН ================
# ======================================
TOKEN = '8451839561:AAE86eHRXSO5G1Tg7DBJSeP7lHbz8q_iLZg'
bot = telebot.TeleBot(TOKEN)

# ======================================
# ==== КОМАНДА /START ==================
# ======================================
@bot.message_handler(commands=['start'])
def start(message):
    username = message.from_user.username or 'NoUsername'
    
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
# ==== ЗАПУСК БОТА =====================
# ======================================
if __name__ == "__main__":
    print("✅ Бот запущен")
    print("🌐 Сайт: https://swagabot.github.io/Swaga/")
    
    # Защита от падений
    import time
    while True:
        try:
            bot.polling(none_stop=True, interval=0, timeout=20)
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            time.sleep(5)
            print("🔄 Перезапуск...")