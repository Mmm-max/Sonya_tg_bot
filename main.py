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

def get_category_keyboard(questions: List[Tuple[int, str]], category_id: int):
    print(questions)
    buttons = [
        [InlineKeyboardButton(text=f"{question[0] + 1}. {question[1]}", 
                              callback_data=f"question_{category_id}_{question[0]}")]
         for question in questions
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@dp.callback_query(F.data.startswith("topic_"))
async def handler_category_selection(callback_query: CallbackQuery):
    category_id = int(callback_query.data.split("_")[1])
    category = data["topics"][category_id]
    category_name = category["name"]
    logger.info(f"user chouse category with id {category_id}, category_name: {category_name}")
    questions = [(i["local_id"], i["question"]) for i in category["questions"]]
    await callback_query.message.answer(
        f"Вы выбрали категорию {category_name}\n",
        reply_markup=get_category_keyboard(questions, category_id)
        )

@dp.callback_query(F.data.startswith("question_"))
async def handler_question_selection(callback_query: CallbackQuery):
    category_id, question_id = list(map(int, callback_query.data.split("_")[1:]))
    logger.info(f"get question with id: {question_id} and category_id: {category_id}")
    category = data["topics"][category_id]
    answer = category["questions"][question_id]["answer"]
    await callback_query.message.answer(
        f"{answer}"
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