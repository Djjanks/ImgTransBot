import asyncio
import re
import logging
from time import sleep
import urllib.request

from PIL import Image
from .chat_dispatcher import ChatDispatcher, ExUnknownCommand
from utils.utils import merge_img
from aiogram import Bot, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import Dispatcher, FSMContext
from aiogram.utils import executor
from aiogram.utils.executor import start_webhook
from bot.settings import BOT_TOKEN, MODE

from torchvision.utils import save_image

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



if MODE in ('LOCAL', 'HEROKU'):

    #STARTUP
    # async def on_startup(_):
    #     print('Bot is online')

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
                    + "/pretrainstyle - присвоить изображения стиль выбранного художника\n"
                    + "/testasync - тестирование асинхронности"
                )
            elif message.text == '/anystyle':
                await message.answer(
                    "Напарвьте первое изображение, стиль которого хотите поменять"
                )

                photo_message = await get_message()
                if 'photo' not in  photo_message:
                    raise ExUnknownCommand()

                photo_file = await bot.get_file(photo_message.photo[-1].file_id)
                content_img = Image.open(urllib.request.urlopen('https://api.telegram.org/file/bot'+BOT_TOKEN+'/'+photo_file.file_path))
                print(content_img)

                await message.answer(
                    "Напарвьте второе изображение, стиль которого будет применены к первому изображению"
                )

                photo_message = await get_message()
                if 'photo' not in  photo_message:
                    raise ExUnknownCommand()

                photo_file = await bot.get_file(photo_message.photo[-1].file_id)
                style_img = Image.open(urllib.request.urlopen('https://api.telegram.org/file/bot'+BOT_TOKEN+'/'+photo_file.file_path))
                # print(style_img)
                
                # img_for_send = test_img(style_img)
                # print(img_for_send)
                img_for_send = await merge_img(content_img, style_img)
                # save_image(img_for_send, "./out111.jpg", nrow=1)
                
                # await photo_message.answer_photo(style_img)
                await photo_message.answer('Картинка сделана')
                await bot.send_photo(chat_id=photo_message.from_user.id,photo=img_for_send)
            
            elif message.text == '/testasync':
                await message.answer(
                    "Запущен тест асинхроннсти. Процесс займет 1 минуту."
                )

                asyncio.sleep(60)

                await message.answer(
                    "Тест окончен."
                )
            else:
                raise ExUnknownCommand()


            # first = await get_message()
            # if not re.match("^\d+$", str(first.text)):
            #     await first.answer("это не число, начните сначала: /start")
            #     return

            # await first.answer("Введите второе число")
            # second = await get_message()

            # if not re.match("^\d+$", str(second.text)):
            #     await second.answer("это не число, начните сначала: /start")
            #     return

            # result = int(first.text) + int(second.text)
            # await second.answer("Будет %s (/start - сначала)" % result)

        except ChatDispatcher.ExTimeout as tb:
            await tb.last_message.answer(
                    "Время ожидания команды превышено. Текущее состояние сброшено.\n"
                    + "Доступны следущие команды:\n"
                    + "/anystyle - присвоить первому изображению стиль второго\n"
                    + "/pretrainstyle - присвоить изображения стиль выбранного художника\n"
                    + "/testasync - тестирование асинхронности"
                )

        except ExUnknownCommand:
            await message.answer(
                    "Команды не найдено.\n"
                    + "Доступны следущие команды:\n"
                    + "/anystyle - присвоить первому изображению стиль второго\n"
                    + "/pretrainstyle - присвоить изображения стиль выбранного художника\n"
                    + "/testasync - тестирование асинхронности"
                )

    chat_dispatcher = ChatDispatcher(chatcb=chat, inactive_timeout=15*60)

    @dp.message_handler()
    async def message_handle(message: types.Message):
        await chat_dispatcher.handle(message)

    @dp.message_handler(content_types=['photo'], state=None)
    async def message_handle(message: types.Message):
        await chat_dispatcher.handle(message)

    # async def on_startup(dp):
    #     logging.warning("Starting connection. ")
    #     await bot.set_webhook(WEBHOOK_URL, drop_pending_updates=True)

# elif MODE == "HEROKU":
#     # STATES
#     class FSMPics(StatesGroup):
#         got_first_pic = State()

#     # COMMANDS
#     @dp.message_handler(commands=["start"])
#     async def commands_start(message: types.Message):
#         await message.reply(
#             "Привет! Я умею изменять стиль картинки.\n"
#             + "Доступны следущие каманды:\n"
#             + "/help - вывести все возможные команды\n"
#             + "/anystyle - присвоить первой картинке стиль второй"
#         )

#     @dp.message_handler(commands=["help"])
#     async def commands_start(message: types.Message):
#         await message.reply(
#             "Доступны следущие каманды:\n"
#             + "/help - вывести все возможные команды\n"
#             + "/anystyle - присвоить первой картинке стиль второй"
#         )

#     @dp.message_handler(commands=["anystyle"])
#     async def commands_start(message: types.Message):
#         await message.reply("Напарвьте первую картинку, стиль которой хотите поменять")

#     # PICS
#     # @dp.message_handler(content_types=['photo'], state=None)
#     # async def messages_first_pic(message: types.Message, state: FSMContext):
#     #     await message.photo[-1].download('image.jpg')
#     #     await message.reply('Good. Send one more pic')
#     #     await FSMPics.got_first_pic.set()

#     # @dp.message_handler(content_types=['photo'], state=FSMPics.got_first_pic)
#     # async def messages_second_pic(message: types.Message, state: FSMContext):
#     #     await message.photo[-1].download('mark.jpg')
#     #     await message.reply('Good. We got two pics')
#     #     merger()
#     #     result = open('C:/Users/admin/Desktop/dev/tbot003/result.jpg','rb')
#     #     await bot.send_photo(message.chat.id, result)
#     #     await state.finish()

#     @dp.message_handler()
#     async def echo(message: types.Message):
#         logging.warning(f"Recieved a message from {message.from_user}")
#         await bot.send_message(message.chat.id, message.text)


#     async def on_startup(dp):
#         logging.warning("Starting connection. ")
#         await bot.set_webhook(WEBHOOK_URL, drop_pending_updates=True)


# async def on_shutdown(dp):
#     logging.warning("Bye! Shutting down webhook connection")


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