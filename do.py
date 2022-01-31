''' Run a function by ado <func_name> '''
import os
print(1)
print('BOT_TOKEN', os.getenv('BOT_TOKEN'))
def set_hook():
    import asyncio
    from bot.settings import HEROKU_APP_NAME, WEBHOOK_URL, BOT_TOKEN
    from aiogram import Bot
    bot = Bot(token=BOT_TOKEN)

    async def hook_set():
        if not HEROKU_APP_NAME:
            print('You have forgot to set HEROKU_APP_NAME')
            quit()
        await bot.set_webhook(WEBHOOK_URL)
        print(await bot.get_webhook_info())
    
    asyncio.run(hook_set())
    bot.close()


def start():
    from bot.bot import main
    print(12)
    main()

print(2)
start()