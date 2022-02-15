import logging
import urllib.request

from PIL import Image
from .chat_dispatcher import ChatDispatcher, ExUnknownCommand
from utils.utils import neural_style_transfer
from aiogram import Bot, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor
from aiogram.utils.executor import start_webhook
from bot.settings import BOT_TOKEN, MODE



if MODE=='HEROKU':
    from bot.settings import (
        BOT_TOKEN,
        HEROKU_APP_NAME,
        MODE,
        WEBHOOK_URL,
        WEBHOOK_PATH,
        WEBAPP_HOST,
        WEBAPP_PORT,
    )

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())


# STARTUP
if MODE =='LOCAL':
    async def on_startup(_):
        print('Bot is online')
elif MODE == 'HEROKU':
    async def on_startup(_):
        logging.warning("Starting connection. ")
        await bot.set_webhook(WEBHOOK_URL, drop_pending_updates=True)

async def chat(get_message):
    try:
        message = await get_message()
        # print(message.text)
        # print(message.PhotoSize)
        if message.text in ('/help', '/start'):
            await message.answer(
                "Приветствую! Я умею изменять стиль картинки.\n"
                + "Доступны следущие команды:\n"
                + "/anystyle - присвоить первому изображению стиль второго\n"
                + "Дополнительные пункты в разработке."
            )
        elif message.text == '/anystyle':
            await message.answer(
                "Напарвьте первое изображение, стиль которого хотите поменять. Размер может быть любым, однако будет принудительно ужато."
            )

            photo_message = await get_message()
            if 'photo' not in  photo_message:
                raise ExUnknownCommand()

            photo_file = await bot.get_file(photo_message.photo[-1].file_id)
            content_img = Image.open(urllib.request.urlopen('https://api.telegram.org/file/bot'+BOT_TOKEN+'/'+photo_file.file_path))
            # print(content_img)

            await message.answer(
                "Напарвьте второе изображение, стиль которого будет применены к первому изображению. Его размер будет автоматически подогнан к первой картинке отзеркаливанием."
            )

            photo_message = await get_message()
            if 'photo' not in  photo_message:
                raise ExUnknownCommand()
            await message.answer(
                "Началась работа над преоразованием изображения. Это может заннять около 10 минут."
            )
            # try:
            photo_file = await bot.get_file(photo_message.photo[-1].file_id)
            style_img = Image.open(urllib.request.urlopen('https://api.telegram.org/file/bot'+BOT_TOKEN+'/'+photo_file.file_path))

            img_for_send = await neural_style_transfer(content_img, style_img)

            await photo_message.answer('Изображение готово!')
            await bot.send_photo(chat_id=photo_message.from_user.id,photo=img_for_send)
            # except:
            #     await message.answer(
            #     "Произошла какая-то ошибка. Попробуйте другие изображения."
            # )

        else:
            raise ExUnknownCommand()

    except ChatDispatcher.ExTimeout as tb:
        await tb.last_message.answer(
                "Время ожидания команды превышено. Текущее состояние сброшено.\n"
                + "Доступны следущие команды:\n"
                + "/anystyle - присвоить первому изображению стиль второго\n"
            )

    except ExUnknownCommand:
        await message.answer(
                "Команды не найдено.\n"
                + "Доступны следущие команды:\n"
                + "/anystyle - присвоить первому изображению стиль второго\n"
            )

chat_dispatcher = ChatDispatcher(chatcb=chat, inactive_timeout=5*60)

@dp.message_handler()
async def message_handle(message: types.Message):
    await chat_dispatcher.handle(message)

@dp.message_handler(content_types=['photo'], state=None)
async def message_handle(message: types.Message):
    await chat_dispatcher.handle(message)

def main():
    logging.basicConfig(level=logging.ERROR)
    if MODE == "HEROKU":
        start_webhook(
            dispatcher=dp,
            webhook_path=WEBHOOK_PATH,
            skip_updates=True,
            on_startup=on_startup,
            host=WEBAPP_HOST,
            port=WEBAPP_PORT,
        )
    elif MODE == "LOCAL":
        executor.start_polling(dp, skip_updates=True, on_startup=on_startup)