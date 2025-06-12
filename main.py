import asyncio
import json
import logging
import os

from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from config import BOT_TOKEN, DATA_FILE_PATH, START_MESSAGE
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram import F

from typing import List, Tuple


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

data =  {}

async def load_data():
    global data
    try:
        with open(DATA_FILE_PATH, "r", encoding="utf-8") as file:
            data = json.load(file)
        logger.info("dataset is upload!")
    except FileNotFoundError:
        logger.error(f"error: file {DATA_FILE_PATH} not found.")
        data = {"topics": []}
    except json.JSONDecodeError:
        logger.error(f"error: file {DATA_FILE_PATH} couldn't be decode")
        data = {"topics": []}

def get_main_menu_keyboard():
    # Формируем кнопки по всем топикам из data["topics"]
    buttons = [
        [InlineKeyboardButton(text=topic["name"], callback_data="topic_" + str(topic["id"]))]
        for topic in data.get("topics", [])
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@dp.message(CommandStart())
async def handle_start(message: types.Message):
    await message.reply(
        START_MESSAGE,
        reply_markup=get_main_menu_keyboard()
    )

def get_category_keyboard(questions: List[Tuple[int, str]]):
    print(questions)
    buttons = [
        [InlineKeyboardButton(text=f"{question[0]}. {question[1]}", 
                              callback_data=f"question_{question[0]}")]
         for question in questions
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@dp.callback_query(F.data.startswith("topic_"))
async def handler_category_selection(callback_query: CallbackQuery):
    category_id = int(callback_query.data.split("_")[1])
    category = data["topics"][category_id]
    category_name = category["name"]
    logger.info(f"user chouse category with id {category_id}, category_name: {category_name}")
    questions = [(i["id"], i["question"]) for i in category["questions"]]
    await callback_query.message.answer(
        f"Вы выбрали категорию {category_name}\n",
        reply_markup=get_category_keyboard(questions)
        )

async def main():
    await load_data()
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен вручную")
    except Exception as e:
        logger.error(f"error {e}")