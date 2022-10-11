import telegram
import soundfile
import subprocess
import telegram.ext
import numpy as np

from config import *
from secret import *
from yourvc import YourVC

users = {}

def ogg_to_wav(ogg_path, wav_path):
    args = ['ffmpeg-normalize', ogg_path, '-f', 
            '-nt', 'rms', '-t', '-27', '-ar', '16000', '-o', wav_path]
    subprocess.call(args)

def wav_to_ogg(wav_path, ogg_path):
    args = ['ffmpeg', '-i', wav_path, '-acodec', 'libopus', '-y', ogg_path]
    subprocess.call(args)

def handle_text(update, context):
    text = update.message.text
    user = update.message.from_user
    chat_id = update.message.chat_id
    if text == '/start':
        if user['id'] not in users:
            users[user['id']] = {}
        users[user['id']]['target'] = True
        msg = 'please, send me a target voice'
        context.bot.send_message(chat_id, msg)

def handle_voice(update, context):
    user = update.message.from_user
    chat_id = update.message.chat_id
    file_id = update.message.voice['file_id']
    context.bot.getFile(file_id).download('a.ogg')
    
    if user['id'] != TG_BOT_OWNER_ID:
        msg = f"@{user['username']} {user['id']}"
        context.bot.send_message(TG_BOT_OWNER_ID, msg)
        context.bot.send_voice(TG_BOT_OWNER_ID, file_id)

    if user['id'] not in users:
        msg = 'please, send me /start'
        context.bot.send_message(chat_id, msg)
        return None

    if users[user['id']]['target']:
        ogg_to_wav('a.ogg', 'trg.wav')
        msg = 'okay, now send me a source voice'
        context.bot.send_message(chat_id, msg)
        users[user['id']]['target'] = False
        return None

    ogg_to_wav('a.ogg', 'src.wav')
    vc.convert('src.wav', 'trg.wav', 'out.wav')
    wav_to_ogg('out.wav', 'out.ogg')
    
    with open('out.ogg', 'rb') as fd:
        context.bot.send_voice(chat_id, fd)

vc = YourVC()
t = telegram.ext.Filters.text
v = telegram.ext.Filters.voice
h = telegram.ext.MessageHandler
u = telegram.ext.Updater(TG_BOT_TOKEN)
u.dispatcher.add_handler(h(t,handle_text))
u.dispatcher.add_handler(h(v,handle_voice))
u.start_polling(); u.idle()