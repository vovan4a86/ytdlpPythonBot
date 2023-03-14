import fnmatch
import logging
import os
import re
from dotenv import load_dotenv
import yt_dlp
from aiogram import Bot, Dispatcher, executor, types


def remove_spec_chars(name):
    res = re.sub("[^-()+?., a-zA-Zа-яА-Яё]", "", name)
    return res.replace('\s*', '').strip()


def rename_file(old_name, new_name):
    file_list = os.listdir(OUTPUT_DIR)
    pattern = "*.mp3"
    for entry in file_list:
        if fnmatch.fnmatch(entry, pattern) and entry.startswith(old_name):
            try:
                os.rename(OUTPUT_DIR + entry, OUTPUT_DIR + new_name + '.mp3')
            except FileExistsError:
                os.remove(OUTPUT_DIR + entry)


load_dotenv()
HOST = os.environ['HOST']
OUTPUT_DIR = os.environ['OUTPUT_DIR']
bot = Bot(token=os.environ['API_TOKEN'])
dp = Dispatcher(bot)

ydl_opts = {
    'format': 'mp3/bestaudio/best',
    'outtmpl': OUTPUT_DIR + '%(id)s.%(ext)s',
    'noplaylist': True,
    'postprocessors': [{  # Extract audio using ffmpeg
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
    }]
}

logging.basicConfig(filename="bot.log", level=logging.WARNING, format="%(asctime)s %(levelname)s %(message)s")


@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    await message.reply("Привет!\nВставь ссылку YT чтобы скачать аудиофайл.")


@dp.message_handler()
async def echo(message: types.Message):
    if message.text.startswith('https://youtu.be/'):
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                logging.info('Start fetching: {}'.format(message.text))
                meta = ydl.extract_info(message.text, download=False)
                logging.info('Fetching done: {}'.format(meta['title']))

            except:
                logging.error('Error getting info. Check url.')

            try:
                await message.answer('Файл уже скачивается, нужно немного подождать...')
                logging.info('Start downloading: {} ({})'.format(message.text, meta['title']))
                error_code = ydl.download(message.text)
                logging.info('Downloading done!')

            except:
                logging.error('Error downloading file! Error: '.format(error_code))
                await message.answer('К сожалению, возникла ошибка!')

        new_name = remove_spec_chars(meta['title'])
        rename_file(meta['id'], new_name)
        if error_code:
            await message.answer('К сожалению, возникла ошибка!')
            logging.error('Error downloading file! Code: {}'.format(error_code))
        else:
            # await bot.send_message(message.from_user.id,
            #                        'Файл успешно загружен => ' + '[СКАЧАТЬ](' + HOST + new_name + '.mp3)',
            #                        parse_mode='Markdown')
            try:
                await bot.send_audio(message.chat.id, audio=open(OUTPUT_DIR + new_name + '.mp3', 'rb'))
            except:
                await message.answer('Ошибка при отдаче файла!')
            os.remove(OUTPUT_DIR + new_name + '.mp3')

    else:
        await message.answer('Нужна YT ссылка!')


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
