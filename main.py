import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.keyboard import InlineKeyboardBuilder
import yt_dlp
import os

# Токениңизди бул жерге жазасыз
TOKEN = "8948619998:AAGgsQYXpWvFmOgS4T5j92KhvSCA68QDmZw"
# Администратордун Telegram ID'син жазыңыз
ADMIN_ID = 6704696780 # Өзүңүздүн ID'ңизди жазыңыз

bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Колдонуучулардын санын сактоо үчүн база
users_set = set()

# Downloads папкасы жок болсо түзүп коёбуз
if not os.path.exists("downloads"):
  os.makedirs("downloads")


# 1. /start командасы
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
  user_id = message.from_user.id
  users_set.add(user_id)

  welcome_text = (
      f"Салам, {message.from_user.first_name}! 👋\n\n"
      "Бул бот аркылуу сиз **Instagram'дан** видео жана музыкаларды оңой эле"
      " жүктөп ала аласыз. 📥\n\n"
      "📌 Жөн гана Instagram шилтемесин жибериңиз!"
  )
  await message.answer(welcome_text)


# 2. Админ үчүн статистика (/stats)
@dp.message(Command("stats"))
async def cmd_stats(message: types.Message):
  if message.from_user.id == ADMIN_ID:
    total_users = len(users_set)
    await message.answer(
        f"📊 **Статистика:**\n\nБотту колдонгон уникалдуу колдонуучулар"
        f" саны: {total_users} киши."
    )
  else:
    await message.answer("Бул буйрук тек гана администратор үчүн! ❌")


# 3. Шилтеме келгенде баскычтарды чыгаруу
@dp.message()
async def check_link(message: types.Message):
  url = message.text
  if "instagram.com" in url:
    users_set.add(message.from_user.id)

    builder = InlineKeyboardBuilder()
    builder.button(text="🎬 Видео жүктөө", callback_data=f"video|{url}")
    builder.button(text="🎵 Музыка жүктөө", callback_data=f"audio|{url}")
    builder.adjust(1)

    await message.answer(
        "Эмнени жүктөп алгыңыз келет? Төмөнкүлөрдүн бирин тандаңыз:",
        reply_markup=builder.as_markup(),
    )
  else:
    await message.answer("Сураныч, туура Instagram шилтемесин жибериңиз.")


# 4. Кнопканы басканда иштөөчү бөлүк
@dp.callback_query()
async def process_callback(callback: types.CallbackQuery):
  data = callback.data
  action, url = data.split("|", 1)

  await callback.message.edit_text("⏳ Жүктөлүүдө, сураныч күтө туруңуз...")

  filename = None
  try:
    # cookies.txt файлы бар же жок экенин текшерип, параметрге кошобуз
    ydl_base_opts = {
        "outtmpl": "downloads/%(id)s.%(ext)s",
        "noplaylist": True,
    }
    if os.path.exists("cookies.txt"):
      ydl_base_opts["cookiefile"] = "cookies.txt"

    if action == "video":
      ydl_opts = {**ydl_base_opts, "format": "best"}
      with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)

      await callback.message.answer_video(types.FSInputFile(filename))

    elif action == "audio":
      ydl_opts = {
          **ydl_base_opts,
          "format": "bestaudio/best",
          "postprocessors": [{
              "key": "FFmpegExtractAudio",
              "preferredcodec": "mp3",
              "preferredquality": "192",
          }],
      }
      with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
        filename = filename.rsplit(".", 1)[0] + ".mp3"

      await callback.message.answer_audio(types.FSInputFile(filename))

    # Күтө турсун билдирүүсүн өчүрүү
    await bot.delete_message(
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
    )

  except Exception as e:
    await callback.message.answer(
        f"❌ Ката кетти: {e}\n\n(Эскертүү: Instagram'дын логин катасы чыкса,"
        " ботко cookies.txt кошуу керек болушу мүмкүн)."
    )

  # Жүктөлүп бүткөн файлды серверден өчүрүп тазалоо (орун албаш үчүн)
  if filename and os.path.exists(filename):
    try:
      os.remove(filename)
    except:
      pass


# Ботту иштетүү
async def main():
  print("Бот ишке кирди...")
  await dp.start_polling(bot)


if __name__ == "__main__":
  import asyncio

  asyncio.run(main())
