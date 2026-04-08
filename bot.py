import json
import os
from flask import Flask, request, jsonify
from telegram import Bot, Update
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, filters

# --- НАСТРОЙКИ ---
BOT_TOKEN = "8442204653:AAHwUFaMToLVyuaUIxoQn8vd64kyCUVZytg"
ADMIN_ID = 6706047006

# --- ИНИЦИАЛИЗАЦИЯ ---
bot = Bot(token=BOT_TOKEN)
app = Flask(__name__)
dispatcher = Dispatcher(bot, None, workers=0)

# Хранилище балансов (временно)
balances = {}

# --- ОБРАБОТЧИК СООБЩЕНИЙ ОТ АДМИН-ПАНЕЛИ (ЧЕРЕЗ sendData) ---
async def handle_web_app_data(update: Update, context):
    if not update.effective_message or not update.effective_message.web_app_data:
        return
    try:
        data = json.loads(update.effective_message.web_app_data.data)
        if data.get('type') == 'admin_deposit':
            if update.effective_user.id != ADMIN_ID:
                return
            user_id = str(data.get('targetId'))
            amount = int(data.get('amount'))
            balances[user_id] = balances.get(user_id, 0) + amount
            await update.message.reply_text(f"✅ Начислено {amount} ₽ пользователю {user_id}")
            try:
                await bot.send_message(user_id, f"🎉 Ваш баланс пополнен на {amount} ₽!")
            except Exception as e:
                print(f"Не удалось отправить сообщение пользователю {user_id}: {e}")
    except Exception as e:
        print(f"Ошибка обработки данных: {e}")

# Регистрируем обработчик для данных из мини-приложения
dispatcher.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_web_app_data))

# --- ВЕБ-ХУК (ПРИЁМ СООБЩЕНИЙ ОТ TELEGRAM) ---
@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        update = Update.de_json(request.get_json(force=True), bot)
        dispatcher.process_update(update)
        return jsonify({"status": "ok"})
    except Exception as e:
        print(f"Ошибка в вебхуке: {e}")
        return jsonify({"status": "error"}), 500

# --- ПРОСТОЙ ЭНДПОИНТ ДЛЯ ПРОВЕРКИ РАБОТЫ ---
@app.route('/')
def home():
    return "Bot is running!", 200

# --- ЗАПУСК ВЕБ-СЕРВЕРА ---
if __name__ == '__main__':
    # Устанавливаем вебхук при старте
    webhook_url = f"https://{os.environ.get('RENDER_EXTERNAL_HOSTNAME', 'localhost')}/webhook"
    bot.set_webhook(webhook_url)
    print(f"Webhook set to {webhook_url}")
    
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
