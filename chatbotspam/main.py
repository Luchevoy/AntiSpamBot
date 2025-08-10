from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
import asyncio
import logging
from antispam import AntiSpam
from captcha import CaptchaSystem

# Настройки бота
TOKEN = "Тут ваш токен"
ADMIN_IDS = []  # ID администраторов
WHITELIST_IDS = []  # ID пользователей с разрешением ссылок

# Инициализация
bot = Bot(token=TOKEN)
dp = Dispatcher()
antispam = AntiSpam()
captcha = CaptchaSystem()

# Логирование
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def notify_chat(chat_id: int, text: str):
    """Отправляет уведомление в чат"""
    try:
        await bot.send_message(chat_id=chat_id, text=text)
    except Exception as e:
        logger.error(f"Ошибка отправки уведомления: {e}")

@dp.message(F.new_chat_members)
async def new_members_handler(message: Message):
    """Новые участники чата"""
    for user in message.new_chat_members:
        if not captcha.is_verified(user.id, ADMIN_IDS, WHITELIST_IDS):
            await captcha.send_captcha(bot, message.chat.id, user.id, user.username)
            await notify_chat(message.chat.id, f"👋 {user.first_name}, пройдите проверку чтобы писать в чат")

@dp.callback_query(F.data.startswith("captcha_"))
async def captcha_handler(callback: CallbackQuery):
    """Обработка капчи"""
    success = await captcha.handle_captcha_callback(callback, ADMIN_IDS, WHITELIST_IDS)
    if success:
        try:
            await callback.message.delete()
            await callback.answer("✅ Проверка пройдена!", show_alert=True)
        except Exception as e:
            logger.error(f"Ошибка обработки капчи: {e}")

@dp.message(F.text | F.caption)
async def message_handler(message: Message):
    """Обработка всех сообщений"""
    user = message.from_user
    chat_id = message.chat.id
    
    # Проверка верификации
    if not captcha.is_verified(user.id, ADMIN_IDS, WHITELIST_IDS):
        try:
            await message.delete()
            if user.id not in captcha.pending_captcha:
                await captcha.send_captcha(bot, chat_id, user.id, user.username)
            return
        except Exception as e:
            logger.error(f"Ошибка удаления сообщения: {e}")
        return
    
    # Для привилегированных пользователей отключаем проверки
    if user.id in ADMIN_IDS or user.id in WHITELIST_IDS:
        return
    
    # Обновляем статистику активности
    is_spam = antispam.update_activity(user.id)
    
    # Проверка на спам
    if antispam.is_spamming(user.id) or is_spam:
        try:
            await message.delete()
            await notify_chat(chat_id, f"🚫 Сообщение от {user.first_name} удалено за спам")
            return
        except Exception as e:
            logger.error(f"Ошибка удаления спама: {e}")
            return
    
    # Проверка на ссылки
    text = message.text or message.caption or ""
    if antispam.has_links(text):
        try:
            await message.delete()
            await notify_chat(chat_id, f"🔗 Сообщение от {user.first_name} удалено (запрещены ссылки)")
            logger.info(f"Удалена ссылка от {user.id}")
        except Exception as e:
            logger.error(f"Ошибка удаления ссылки: {e}")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())