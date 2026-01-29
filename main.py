import asyncio
import os
from aiogram import Bot, Dispatcher
from app.handlers import router

from dotenv import load_dotenv

# load env file 
load_dotenv()

BOT_TOKEN = os.getenv("BOT-API-KEY") 

# --- Main start function ---

async def main():
    
    # Object init
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    
    # Router connection to dispatcher
    dp.include_router(router)
     
    # skip_updates=True гарантує, що бот проігнорує повідомлення,
    # які були надіслані, поки він був офлайн.
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        print("Starting bot...")
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot stopped by user.")
    except Exception as e:
        print(f"An error occurred: {e}")