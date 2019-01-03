import logging
import textwrap
import uuid

import telegram
from sqlalchemy.orm.exc import NoResultFound
from telegram.ext import MessageHandler
from telegram.ext.filters import Filters

from step_bot.handlers import BaseHandler
from step_bot.models import Chat


class GroupHandler(BaseHandler):
    greetings_text = textwrap.dedent("""\
    
    Идея проекта проста. Все мы движемся, чтобы жить. Без движения нет Жизни ни в частном, ни в общем понимании. Но часто мы забываем об этой простой истине и наша жизнь превращается в рутину из минимальных движений работа-дом-работа. 

    Проект создан для людей, которые хотят вырваться из этого порочного круга и начать жить более здоровой, активной и насыщенной событиями жизнью.

    *Как мы это делаем?*
    - Участники проекта ставят общую на всех цель в километрах (например, сейчас это 40 000 км до 1 марта 2019 – первого дня весны). И в течение дня каждый участник старается пройти, пробежать, проползти))) максимальное для себя количество шагов в меру своих сил, возможностей и физического состояния. 🚶‍♀🚶‍♂🏃‍♀🏃‍♂
    - В конце дня, до 24:00, мы скидываем свои результаты в виде команд (/today и /day) для нашего бота, который ведет подсчет. Результаты можно собирать при помощи программ для смартфона (например Samsung Health, Apple Здоровье, Pacer https://play.google.com/store/apps/details?id=cc.pacer.androidapp ) или фитнес-трекеров. 📱⌚️
    - Все результаты автоматически подсчитываются при помощи бота, отчеты в краткой форме публикуются ежедневно в конце дня. За бота отвечает @polyn0m, по мере его занятости буду добавляться всякие плюшки к боту.
    
    *Для чего все это нужно?*
    - Мы считаем, что в одной дружной команде добиться цели гораздо проще и быстрее чем в одиночку. 👬👫👭
    - Каждый из нас работает над собой, своей активностью и улучшает свои жизненные показатели, поддерживает других не только лично для себя, но и для общего результата.

    *Чтобы потом сказать "Мы вместе Это сделали!"* 💪 🏆💥🌟💫
    """)

    def __init__(self, *args, **kwargs):
        super(GroupHandler, self).__init__(*args, **kwargs)

        self.dispatcher.add_handler(MessageHandler(Filters.status_update.chat_created, self.chat_created))
        self.dispatcher.add_handler(MessageHandler(Filters.status_update.migrate, self.chat_migrate))
        self.dispatcher.add_handler(MessageHandler(Filters.status_update.new_chat_members, self.new_member))

    def __create_chat(self, bot, chat_id):
        db_session = self.get_db()

        try:
            db_session.query(Chat).filter(Chat.chat_id == str(chat_id)).one()
        except NoResultFound:
            new_chat = Chat(id=uuid.uuid4(), chat_id=chat_id)

            db_session.add(new_chat)
        finally:
            bot.send_message(
                chat_id=chat_id, text=textwrap.dedent("""\
                Всем привет!

                Меня зовут *%s*, я запомнил ваш чат!
                Нужно установить цель для этой дружной команды!
                """ % bot.first_name), parse_mode=telegram.ParseMode.MARKDOWN
            )

            db_session.commit()

    def __migrate_chat(self, chat_id, new_chat_id):
        db_session = self.get_db()

        try:
            chat = db_session.query(Chat).filter(Chat.chat_id == str(chat_id)).one()

            chat.chat_id = new_chat_id
        except NoResultFound:
            pass
        finally:
            db_session.commit()

    def chat_created(self, bot, update):
        logging.debug('New chat created %s' % update.message.chat_id)

        self.__create_chat(bot, update.message.chat_id)

    def chat_migrate(self, bot, update):
        self.__migrate_chat(update.message.chat_id, update.message.migrate_to_chat_id)

    def new_member(self, bot, update):
        logging.debug('New members in chat %s' % update.message.chat_id)

        members = list(filter(lambda m: not m.is_bot, update.message.new_chat_members))
        i_am = list(filter(lambda m: m.is_bot and m.username == bot.username, update.message.new_chat_members))

        if len(i_am):
            self.__create_chat(bot, update.message.chat_id)

        if len(members) > 1:
            bot.send_message(
                chat_id=update.message.chat_id, text=textwrap.dedent("""\
                *Приветствую всех в челендж-проекте "Шаг к Мечте"!* ✋ {0}
                """.format(self.greetings_text)), parse_mode=telegram.ParseMode.MARKDOWN
            )
        elif len(members) > 0:
            bot.send_message(
                chat_id=update.message.chat_id, text=textwrap.dedent("""\
                *Приветствую тебя в челендж-проекте "Шаг к Мечте"!* ✋ {0}
                """.format(self.greetings_text)), parse_mode=telegram.ParseMode.MARKDOWN
            )


class P2PEchoHandler(BaseHandler):
    def __init__(self, *args, **kwargs):
        super(P2PEchoHandler, self).__init__(*args, **kwargs)

        self.dispatcher.add_handler(MessageHandler(Filters.private, self.p2p_warning))

    def p2p_warning(self, bot, update):
        logging.debug('Someone write me in p2p chat, suck it!')

        bot.send_message(
            chat_id=update.message.chat_id, text="""
            Я предназначен только для групповых чатов! Так что вначале добавь меня в группу!
            """
        )
