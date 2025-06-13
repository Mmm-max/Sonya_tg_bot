import asyncio
import json
import logging
import os
from collections import deque

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
user_last_question_msg = {}
user_last_topic_msg = {}
user_last_start_msg = {}

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

async def delete_message(chat_id: int, message_id: int):
    try:
        await bot.delete_message(chat_id, message_id)
    except Exception as e:
        logger.warning(f"Не удалось удалить сообщение {message_id} в чате {chat_id}: {e}")
        
        
@dp.message(CommandStart())
async def handle_start(message: types.Message):
    user_id = message.from_user.id
    last_msg_id = user_last_start_msg.get(user_id)
    if last_msg_id:
        await delete_message(message.chat.id, last_msg_id)
    sent_msg = await message.reply(
        START_MESSAGE,
        reply_markup=get_main_menu_keyboard(),
        parse_mode=ParseMode.HTML
    )
    user_last_start_msg[user_id] = sent_msg.message_id

def get_category_keyboard(questions: List[Tuple[int, str]], category_id: int):
    buttons = [
        [InlineKeyboardButton(text=f"{question[0] + 1}. {question[1]}", 
                              callback_data=f"question_{category_id}_{question[0]}")]
         for question in questions]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@dp.callback_query(F.data.startswith("topic_"))
async def handler_category_selection(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    last_msg_id = user_last_topic_msg.get(user_id)
    if last_msg_id:
       await delete_message(callback_query.message.chat.id, last_msg_id)
    last_msg_ids = user_last_question_msg.get(user_id)
    if last_msg_ids:
        for msg_id, link_id in last_msg_ids:
            await delete_message(callback_query.message.chat.id, msg_id)
            await delete_message(callback_query.message.chat.id, link_id)
        user_last_question_msg[user_id] = deque(maxlen=3)
    category_id = int(callback_query.data.split("_")[1])
    category = data["topics"][category_id]
    category_name = category["name"]
    logger.info(f"user chouse category with id {category_id}, category_name: {category_name}")
    questions = [(i["local_id"], i["question"]) for i in category["questions"]]
    sent_msg = await callback_query.message.answer(
        f"Вы выбрали категорию {category_name}\n",
        reply_markup=get_category_keyboard(questions, category_id)
        )
    user_last_topic_msg[user_id] = sent_msg.message_id
    

@dp.callback_query(F.data.startswith("question_"))
async def handler_question_selection(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    last_msg_ids = user_last_question_msg.get(user_id)
    if last_msg_ids and len(last_msg_ids) == 3:
        msg_id, mgs_link_id = last_msg_ids.popleft()
        await delete_message(callback_query.message.chat.id, msg_id)
        await delete_message(callback_query.message.chat.id, mgs_link_id)

    category_id, question_id = list(map(int, callback_query.data.split("_")[1:]))
    logger.info(f"get question with id: {question_id} and category_id: {category_id}")
    category = data["topics"][category_id]
    answer = category["questions"][question_id]["answer"]
    link = category["questions"][question_id]["link"]
    sent_msg = await callback_query.message.answer(
        f"{answer}"
    )
    sent_link = await callback_query.message.answer(
        f"{link}"
    )
    if last_msg_ids and len(last_msg_ids) < 3:
        user_last_question_msg[user_id].append((sent_msg.message_id, sent_link.message_id))
    else:
        user_last_question_msg[user_id] = deque([(sent_msg.message_id, sent_link.message_id)], maxlen=3)
    
    
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