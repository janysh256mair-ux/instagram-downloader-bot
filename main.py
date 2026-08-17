import asyncio
import logging
import os
import sys
from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message, FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import yt_dlp

TOKEN = "8948619998:AAGgsQYXpWvFmOgS4T5j92KhvSCA68QDmZw"  # Өзүңүздүн токениңиз турсун

dp = Dispatcher()

def get_choice_keyboard(url):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎥 Видео жүктөө", callback_data=f"vid:{url}")],
        [InlineKeyboardButton(text="🎵 Музыка (Аудио) жүктөө", callback_data=f"aud:{url}")]
    ])

@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    await message.answer("Салам! Мага Instagram шилтемесин жибер, мен аны видео же музыка катары жүктөп берем. 📥")

@dp.message()
async def handle_url(message: Message) -> None:
    if "instagram.com" in message.text:
        await message.answer("Эмнени жүктөп алайын?", reply_markup=get_choice_keyboard(message.text))
    else:
        await message.answer("⚠️ Сураныч, туура Instagram шилтемесин жөнөтүңүз.")

@dp.callback_query(F.data.startswith(("vid:", "aud:")))
async def download_callback(callback: CallbackQuery):
    action, url = callback.data.split(":", 1)
    await callback.message.edit_text("⏳ Жүктөлүүдө, күтө туруңуз...")

    file_name = f"download_{callback.from_user.id}"
    
    # FFmpeg талап кылбаган жөнөкөй жана эффективдүү форматтар
    ydl_opts = {
        'format': 'best' if action == "vid" else 'bestaudio',
        'outtmpl': f"{file_name}.{'mp4' if action == 'vid' else 'm4a'}",
        'quiet': True
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        final_file = f"{file_name}.{'mp4' if action == 'vid' else 'm4a'}"
        
        if action == "vid":
            await callback.message.answer_video(video=FSInputFile(final_file), caption="✅ Видео ийгиликтүү жүктөлдү!")
        else:
            await callback.message.answer_audio(audio=FSInputFile(final_file), caption="✅ Музыка ийгиликтүү жүктөлдү!")
        
        await callback.message.delete()
        if os.path.exists(final_file): 
            os.remove(final_file)
        
    except Exception as e:
        await callback.message.answer(f"❌ Ката кетти: Шилтеменин туура экенин текшериңиз.")
        print(f"Ката чоо-жайы: {e}")

async def main() -> None:
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())