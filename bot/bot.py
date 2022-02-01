import asyncio
import re
import logging

from PIL import Image
from .chat_dispatcher import ChatDispatcher
from aiogram import Bot, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import Dispatcher, FSMContext
from aiogram.utils.executor import start_webhook
from bot.settings import (BOT_TOKEN, MODE)
if MODE=='LOCAL':
    from bot.settings import (BOT_TOKEN, HEROKU_APP_NAME, MODE,
                            WEBHOOK_URL, WEBHOOK_PATH,
                            WEBAPP_HOST, WEBAPP_PORT)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())

print(1111111)
if MODE == 'HEROKU':
    async def chat(get_message):
        try:
            message = await get_message()
            await message.answer('Умею складывать числа, введите первое число')

            first = await get_message()
            if not re.match('^\d+$', str(first.text)):
                await first.answer('это не число, начните сначала: /start')
                return

            await first.answer('Введите второе число')
            second = await get_message()

            if not re.match('^\d+$', str(second.text)):
                await second.answer('это не число, начните сначала: /start')
                return

            result = int(first.text) + int(second.text)
            await second.answer('Будет %s (/start - сначала)' % result)

        except ChatDispatcher.Timeout as te:
            await te.last_message.answer('Что-то Вы долго молчите, пойду посплю')
            await te.last_message.answer('сначала - /start')

    chat_dispatcher = ChatDispatcher(chatcb=chat,
                                    inactive_timeout=20)

    @dp.message_handler()
    async def message_handle(message: types.Message):
        await chat_dispatcher.handle(message)
elif MODE == 'LOCAL':
    #STATES
    class FSMPics(StatesGroup):
        got_first_pic = State() 

    #COMMANDS
    @dp.message_handler(commands=['start'])
    async def commands_start(message: types.Message):
        await message.reply('Привет! Я умею изменять стиль картинки.\n'
        +'Доступны следущие каманды:\n'
        +'/help - вывести все возможные команды\n'
        +'/anystyle - присвоить первой картинке стиль второй')

    @dp.message_handler(commands=['help'])
    async def commands_start(message: types.Message):
        await message.reply('Доступны следущие каманды:\n'
        +'/help - вывести все возможные команды\n'
        +'/anystyle - присвоить первой картинке стиль второй')

    @dp.message_handler(commands=['anystyle'])
    async def commands_start(message: types.Message):
        await message.reply('Напарвьте первую картинку, стиль которой хотите поменять')

    #PICS
    # @dp.message_handler(content_types=['photo'], state=None)
    # async def messages_first_pic(message: types.Message, state: FSMContext):
    #     await message.photo[-1].download('image.jpg')
    #     await message.reply('Good. Send one more pic')
    #     await FSMPics.got_first_pic.set()

    # @dp.message_handler(content_types=['photo'], state=FSMPics.got_first_pic)
    # async def messages_second_pic(message: types.Message, state: FSMContext):
    #     await message.photo[-1].download('mark.jpg')
    #     await message.reply('Good. We got two pics')
    #     merger()
    #     result = open('C:/Users/admin/Desktop/dev/tbot003/result.jpg','rb')
    #     await bot.send_photo(message.chat.id, result)
    #     await state.finish()

    @dp.message_handler()
    async def echo(message: types.Message):
        logging.warning(f'Recieved a message from {message.from_user}')
        await bot.send_message(message.chat.id, message.text)


async def on_startup(dp):
    logging.warning(
        'Starting connection. ')
    await bot.set_webhook(WEBHOOK_URL,drop_pending_updates=True)


async def on_shutdown(dp):
    logging.warning('Bye! Shutting down webhook connection')


def main():
    logging.basicConfig(level=logging.INFO)
    if MODE == 'HEROKU':
        start_webhook(
            dispatcher=dp,
            webhook_path=WEBHOOK_PATH,
            skip_updates=True,
            on_startup=on_startup,
            host=WEBAPP_HOST,
            port=WEBAPP_PORT,
        )
