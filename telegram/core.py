from telegram.config import Settings

from aiogram import Bot

from aiogram import Dispatcher, html
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.enums import ParseMode



dp = Dispatcher()

@dp.message(CommandStart())
async def welcome(message: Message) -> None:
    await message.answer(f"Welcome, {html.bold(message.from_user.full_name)}!")

@dp.message()
async def just_address(message: Message) -> None:
    message.text


async def main():
    settings = Settings()
    bot = Bot(
        token=settings.telegram_api_token.get_secret_value(),
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    await dp.start_polling(bot)
