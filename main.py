import os
import random
from vk_bot import VkBot
from dotenv import load_dotenv
from datetime import datetime
from sqlalchemy import func
from db import get_session, User, add_user
import openai

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")


session = get_session()
token = os.getenv('TOKEN')
group_id = os.getenv('GROUP_ID')

session = get_session()
bot = VkBot(token=token, group_id=group_id)
MAX_NICKNAME_LENGTH = 20
MIN_NICKNAME_LENGTH = 5
def profile_handler(event):
    chat_id = event.chat_id,
    user_id = event.object.message['from_id']
    user = session.query(User).filter(User.user_id == user_id).first()
    message = f'🧑🏻 Ник: {user.username}\n'
    message += f'🆔 ID: {user.id}\n'
    message += f'💰 Пив-коинов: {user.beer_coin}\n'
    message += f'🍻 Выпито: {round(user.liters)} л.\n'
    date_str = user.created_at.strftime("%Y-%m-%d")
    message += f'🗓️ Дата регистрации: {date_str}'
    bot.send_message(chat_id, message)


def beer_handler(event):
    chat_id = event.chat_id,
    user_id = event.object.message['from_id']
    name = bot.get_name(user_id)

    user = session.query(User).filter(User.user_id == user_id).first()

    if user is None:
        add_user(user_id, 1, name[1], name[2])
    else:

        # Минимальный интервал времени между действиями
        TIME_BETWEEN_ACTIONS  = 0.5 * 60

        now = datetime.now()

        # Время последней пьянки
        time_since_last_activity = now - user.last_activity
    
        if time_since_last_activity.total_seconds() > TIME_BETWEEN_ACTIONS:

            # Количество выпитого пива
            BEER_AMOUNT_MIN = 6
            BEER_AMOUNT_MAX = 100
            plus = random.uniform(BEER_AMOUNT_MIN, BEER_AMOUNT_MAX)

            # Количество пив-коинов
            BEER_COIN_MIN = 1
            BEER_COIN_MAX = 100
            beer_coins = random.randint(BEER_COIN_MIN, BEER_COIN_MAX)

            beer_amount_range = BEER_AMOUNT_MAX - BEER_AMOUNT_MIN
            beer_amount = BEER_AMOUNT_MIN + (user.liters / 100) * beer_amount_range
            new_random = random.uniform(BEER_AMOUNT_MIN, beer_amount)

            # Обновляем данные
            user.liters += new_random
            user.beer_coin += beer_coins
            user.last_activity = datetime.now()
            session.commit()


            user_new_response = session.query(User)\
                .filter(User.user_id == user_id).first()

            drunk_all = user_new_response.liters
            message = f'[id{user_id}|{name[0]}], ты бахнул {new_random}л. пива.'
            message += f'\nВсего выпито: {round(drunk_all)}л. пива, '
            message += f'и тебе выпало {beer_coins} пив-коинов'
            bot.send_message(chat_id, message)
        else:
            remaining_time = TIME_BETWEEN_ACTIONS - time_since_last_activity.total_seconds()
            minutes, seconds = divmod(remaining_time, 60)
            total_coins = session.query(func.sum(User.beer_coin)).scalar()
            message = f'[id{user_id}|{name[0]}], повтори через '
            message += f'{round(minutes)}м. {round(seconds)}с.\n\n'
            message += f'Выпито всего - {round(user.liters)} л.\n'
            message += f'Пив-коинов в этом чате - {total_coins}'
            bot.send_message(chat_id, message)


def balance_handler(event):
    chat_id = event.chat_id,
    user_id = event.object.message['from_id']
    user = session.query(User).filter(User.user_id == user_id).first()
    name = bot.get_name(user_id)
    message = f'[id{user_id}|{name[0]}], '
    message += f'На данный момент у вас  {user.beer_coin} пив-коинов '
    message += f'{round(user.liters)} литров в этом чате'
    bot.send_message(chat_id, message)


def top_users_handler(event):
    chat_id = event.chat_id,
    users = session.query(User).order_by(User.liters.desc()).limit(10).all()
    message = "🍺 Топ-10 игроков чата:\n"
    for i, user in enumerate(users):
        message += f"{i+1}. [id{user.id}|{user.first_name} "
        message += f"{user.last_name}] - {round(user.liters)} л.\n"
    message_end_text = "Чтобы попасть в этот список, начните игру с помощью команды "
    message_end_text += "/beer\n\n"
    message_end_text += "ТОП лучших игроков - /top"
    bot.send_message(chat_id, f'{message}\n\n')


def change_nick_handler(event):
    chat_id = event.chat_id,
    message = event.object.message['text']
    new_nickname = message.split(" ", 2)[2]
    user_id = event.object.message['from_id']
    name = bot.get_name(user_id)

    if len(new_nickname) > MAX_NICKNAME_LENGTH:
            bot.send_message(chat_id, f'[id{user_id}|{name[0]}], ваш ник не может быть длинее 20 символов 😞')
    if len(new_nickname) < MIN_NICKNAME_LENGTH:
            bot.send_message(chat_id, f'[id{user_id}|{name[0]}], ваш ник не может быть короче 5 символов 😞')

    user = session.query(User).filter_by(user_id=user_id).first()
    user.username = new_nickname
    session.commit()

    # update the nick
    # name in the database
    
    bot.send_message(chat_id, f'Ваш ник изменён на «{new_nickname}»')

def bot_handler(event):
    user_id = event.object.message['from_id']
    chat_id = event.chat_id,
    message = event.object.message['text']
    
    name = bot.get_name(user_id)

    new_text = message.strip("бот")
    bot.send_message(chat_id, f'[id{user_id}|{name[0]}], обрабатываю твой запрос...')
    response = openai.Completion.create(
        model="text-davinci-003",
        prompt=new_text,
        temperature=0.7,
        max_tokens=600,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
        stop=["\"\"\""]
        )

    text = response['choices'][0]['text']
    print(text.strip())
    bot.send_message(chat_id, f'[id{user_id}|{name[0]}], {text.strip()}')


    # update the nick
    # name in the database
    


def help_handler(event):
    chat_id = event.chat_id,
    message = f'ℹ️ Все команды\n'
    message += f'профиль(/profile)\n'
    message += f'пить пиво(/beer)\n'
    message += f'баланс(/balance)\n'
    message += f'топ(/top)\n'
    message += f'статистика(/tstatsop)\n'
    bot.send_message(chat_id, message)

def test_lopata(event):
    user_id = event.object.message['from_id']
    name = bot.get_name(user_id)
    bot.send_message(event.chat_id, f'{name[0]} лопата копает траву')


def main():
    bot.add_command_handler('/profile', profile_handler)
    bot.add_command_handler('/beer', beer_handler)
    bot.add_command_handler('/balance', balance_handler)
    bot.add_command_handler('/top', top_users_handler)
    bot.add_command_handler('/stats', top_users_handler)
    bot.add_command_handler('/help', help_handler)
    bot.add_message_handler('профиль', profile_handler)
    bot.add_message_handler('пить пиво', beer_handler)
    bot.add_message_handler('баланс', balance_handler)
    bot.add_message_handler('топ', top_users_handler)
    bot.add_message_handler('статистика', top_users_handler)
    bot.add_message_handler('сменить ник', change_nick_handler)
    bot.add_message_handler('помощь', help_handler)
    bot.add_message_handler('бот', bot_handler)

    bot.start()





if __name__ == '__main__':
    main()
