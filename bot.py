from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.storage.memory import MemoryStorage
import asyncio
import os
from dotenv import load_dotenv
from logger import ParserLogger
from google_sheets import GoogleSheetsManager
from worker import process_number
from concurrent.futures import ThreadPoolExecutor

load_dotenv()

bot = Bot(token=os.getenv('BOT_TOKEN'))
dp = Dispatcher(storage=MemoryStorage())

parsing_in_progress = False

def get_main_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Старт")]],
        resize_keyboard=True
    )
    return keyboard

async def process_async(number, worker_id, logger, cookie_file, executor):
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        executor, 
        process_number, 
        number, 
        worker_id, 
        logger, 
        cookie_file
    )
    return result

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "Вітаю! Це бот для запуску парсингу.\n\nНатисніть кнопку для запуску парсингу:",
        reply_markup=get_main_keyboard()
    )

@dp.message(F.text == "Старт")
async def start_parsing(message: types.Message):
    global parsing_in_progress
    
    if parsing_in_progress:
        await message.answer("Парсинг вже виконується. Зачекайте його завершення.")
        return
    
    parsing_in_progress = True
    await message.answer("Парсинг почався...")
    
    logger = ParserLogger()
    logger.info('PARSING STARTED FROM BOT')
    
    try:
        sheets = GoogleSheetsManager('credentials.json')
        logger.info(f'Connected to spreadsheet: {sheets.spreadsheet.title}')
        
        numbers = sheets.get_numbers_to_parse()
        logger.info(f'Loaded {len(numbers)} numbers')
        
        if not numbers:
            await message.answer("Не знайдено номерів для парсингу")
            parsing_in_progress = False
            return
        
        max_workers = 3
        all_results = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            tasks = []
            for idx, number in enumerate(numbers):
                task = process_async(number, idx, logger, 'cookie.json', executor)
                tasks.append(task)
            
            results = await asyncio.gather(*tasks)
        
        for result_list in results:
            all_results.extend(result_list)
        
        logger.info(f'Saving {len(all_results)} offers to Google Sheets')
        sheets.save_results(all_results, numbers)
        
        successful = len([n for n in numbers if any(r.get('number') == n for r in all_results)])
        failed = len(numbers) - successful
        
        logger.info(f'COMPLETED: {len(all_results)} offers | Success: {successful} | Failed: {failed}')
        
        await message.answer(
            f"Парсинг закінчився\n\n"
            f"Спарсено:\n"
            f"Успішно: {successful}\n"
            f"Не успішно: {failed}\n\n"
            f"Для наступного запуску натисніть кнопку Старт",
            reply_markup=get_main_keyboard()
        )
        
    except Exception as e:
        logger.exception(f'Bot parsing error: {e}')
        await message.answer(f"Помилка при парсингу: {str(e)}")
    finally:
        parsing_in_progress = False

async def start_bot():
    print("Bot started...")
    await dp.start_polling(bot)