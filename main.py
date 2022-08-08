from telebot import TeleBot

from threading import Thread

import schedule

import redis

import time

from my_secrets import TOKEN

from my_backend import Back, DBInterface


bot = TeleBot(TOKEN)

db = redis.Redis('localhost', 6379, 0, charset="utf-8", decode_responses=True)

back = Back(DBInterface(db), bot)


@bot.message_handler(commands=["play"])
def handle_play(message):
    back.register_user(message.from_user.id)
    bot.send_message(message.from_user.id, "Начинаем поиск.")


@bot.message_handler(commands=["stop"])
def handle_stop(message):
    back.notify_stop(message.from_user.id)
    back.unregister_user(message.from_user.id)


@bot.message_handler()
def handle_messages(message):
    user_id = message.from_user.id

    if back.user_is_playing(user_id):
        back.user_move(user_id, message.text)
        back.notify_move(user_id)
        back.check_game_for_end(user_id)


def do_start_ready_users():
    schedule.every(1).seconds.do(back.start_ready_users)

    while True:
        schedule.run_pending()
        time.sleep(1)


thread = Thread(target=do_start_ready_users)
thread.start()

bot.infinity_polling(skip_pending=True)
