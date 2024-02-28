import os, subprocess
import argparse, asyncio

from TTS.api import TTS
from telegram import Update
from telegram import InputMediaAudio
from telegram.ext import MessageHandler
from telegram.ext import filters, Application

def wav_to_ogg(wav_path, ogg_path):
    subprocess.call([
        'ffmpeg', '-i', wav_path, 
        '-acodec', 'libopus', '-y', ogg_path
    ])

def ogg_to_wav(ogg_path, wav_path):
    subprocess.call([
        'ffmpeg-normalize', ogg_path, '-f', '-nt', 
        'rms', '-t', '-27', '-ar', '16000', '-o', wav_path
    ])

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('id', type=int, help='bot owner id')
    parser.add_argument('token', type=str, help='bot token')
    return parser.parse_args()

def load_model():
    name = 'voice_conversion_models/multilingual/vctk/freevc24'
    return TTS(model_name=name, progress_bar=True).to('cpu')


users = {}
args = parse_args()
model = load_model()

def convert(source_wav, target_wav, file_path):

    params = {
        'file_path': file_path,
        'source_wav': source_wav,
        'target_wav': target_wav
    }

    model.voice_conversion_to_file(**params)


async def handle_text(update, context):

    text = update.message.text
    user = update.message.from_user

    if text == '/start':

        if user['id'] not in users:
            users[user['id']] = {}

        users[user['id']]['target'] = True
        msg = 'please, send me the target voice'
        await update.message.reply_text(msg)
        os.makedirs(str(user['id']), exist_ok=True)


async def handle_voice(update, context):

    voice = update.message.voice
    user = update.message.from_user
    chat_id = update.message.chat_id

    path = f"{user['id']}/voice.ogg"
    file = await context.bot.get_file(voice)
    await file.download_to_drive(path)

    if user['id'] != args.id:
        msg = f"@{user['username']} {user['id']}"
        await context.bot.send_message(args.id, msg)
        await context.bot.send_voice(args.id, voice['file_id'])

    if user['id'] not in users:
        msg = 'please, send me /start'
        await context.bot.send_message(chat_id, msg)

    elif users[user['id']]['target']:
        users[user['id']]['target'] = False
        msg = 'okay, now send me the source voice'
        ogg_to_wav(path, f"{user['id']}/trg.wav")
        await context.bot.send_message(chat_id, msg)

    else:

        paths = (
            f"{user['id']}/src.wav",
            f"{user['id']}/trg.wav",
            f"{user['id']}/out.wav"
        )

        loop = asyncio.get_running_loop()
        ogg_to_wav(path, f"{user['id']}/src.wav")
        await loop.run_in_executor(None, convert, *paths)
        wav_to_ogg(f"{user['id']}/out.wav", f"{user['id']}/out.ogg")

        with open(f"{user['id']}/out.ogg", 'rb') as fd:
            await context.bot.send_voice(chat_id, fd)


app = Application.builder().token(args.token).build()
app.add_handler(MessageHandler(filters.TEXT, handle_text))
app.add_handler(MessageHandler(filters.VOICE, handle_voice))
app.run_polling(allowed_updates=Update.ALL_TYPES)