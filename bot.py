import asyncio
import os
import base64
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_KEY = os.getenv("GEMINI_KEY")

if not TELEGRAM_TOKEN or not GEMINI_KEY:
    raise ValueError("Не найдены токены. Проверь файл .env")

client = AsyncOpenAI(
    api_key=os.getenv("GEMINI_KEY"),
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    timeout=60.0
)

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

SYSTEM_PROMPT = (
    "Ты — эксперт-репетитор, который помогает решать домашние задания. "
    "Пользователь будет присылать тебе задачи по разным предметам. "
    "Твоя задача: решить задачу пошагово, объясняя каждое действие простым языком. "
    "Если это математика — пиши формулы и вычисления. "
    "Если физика — укажи законы и формулы. "
    "Отвечай на русском языке."
    "ВАЖНО: не используй LaTeX-разметку (никаких $\\rightarrow$, $\\Rightarrow$, \\frac и т.п.). "
    "Пиши обычными символами: →, ⇒, дроби словами (например, 1/2). "
    "Используй простое форматирование: звёздочки **жирный**, дефисы для списков."
)

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "Привет! Я бот-решебник. Пришли мне задачу, и я постараюсь её решить."
    )

@dp.message(F.photo)
async def handle_photo(message: types.Message):
    await bot.send_chat_action(message.chat.id, 'typing')

    try:
        photo = message.photo[-1]
        file = await bot.get_file(photo.file_id)
        file_bytes = await bot.download_file(file.file_path)
        b64 = base64.b64encode(file_bytes.read()).decode("utf-8")

        response = await client.chat.completions.create(
            model="gemini-3.8-flash",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Реши задачу с этого фото."},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{b64}"
                            }
                        }
                    ]
                }
            ],
            stream=False
        )

        answer = response.choices[0].message.content
        for i in range(0, len(answer), 4000):
            await message.answer(answer[i:i+4000])

    except Exception as e:
        await message.answer(f"Ошибка при обработке фото: {e}")

@dp.message()
async def handle_message(message: types.Message):
    if not message.text:
        await message.answer("Пожалуйста, отправь текстовое задание.")
        return

    await bot.send_chat_action(message.chat.id, 'typing')

    try:
        response = await client.chat.completions.create(
            model="gemini-3.8-flash",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": message.text}
            ],
            stream=False
        )
        answer = response.choices[0].message.content
        for i in range(0, len(answer), 4000):
            await message.answer(answer[i:i+4000])

    except Exception as e:
        await message.answer(f"Ошибка при решении: {e}")

async def main():
    print("Бот запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())