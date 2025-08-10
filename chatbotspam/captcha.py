import random
import asyncio
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

class CaptchaSystem:
    def __init__(self):
        self.pending_captcha = set()
        self.verified_users = set()

    async def send_captcha(self, bot, chat_id: int, user_id: int, username: str = None, captcha_time: int = 120):
        """Отправляет капчу пользователю"""
        name = f"@{username}" if username else f"ID{user_id}"
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Я человек", callback_data=f"captcha_{user_id}")]
        ])
        
        msg = await bot.send_message(
            chat_id=chat_id,
            text=f"{name}, подтвердите что вы не бот:\nНажмите кнопку ниже чтобы продолжить общение",
            reply_markup=keyboard
        )
        
        self.pending_captcha.add(user_id)
        asyncio.create_task(self.delete_captcha_after_timeout(bot, chat_id, msg.message_id, user_id, captcha_time))

    async def delete_captcha_after_timeout(self, bot, chat_id: int, message_id: int, user_id: int, captcha_time: int):
        """Удаляет капчу после таймаута"""
        await asyncio.sleep(captcha_time)
        
        if user_id in self.pending_captcha:
            try:
                await bot.delete_message(chat_id=chat_id, message_id=message_id)
                self.pending_captcha.remove(user_id)
            except Exception as e:
                print(f"Ошибка удаления капчи: {e}")

    def is_verified(self, user_id: int, admin_ids: list, whitelist_ids: list) -> bool:
        """Проверяет, прошел ли пользователь капчу"""
        return user_id in self.verified_users or user_id in admin_ids or user_id in whitelist_ids

    async def handle_captcha_callback(self, callback, admin_ids: list, whitelist_ids: list):
        """Обрабатывает нажатие на капчу"""
        _, user_id = callback.data.split('_')
        user_id = int(user_id)
        
        if callback.from_user.id != user_id:
            await callback.answer("Эта капча не для вас!")
            return False
        
        if user_id not in self.pending_captcha:
            await callback.answer("Капча уже недействительна!")
            return False
        
        self.verified_users.add(user_id)
        self.pending_captcha.remove(user_id)
        return True