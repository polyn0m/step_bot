import logging
import textwrap
import uuid

import telegram
from sqlalchemy.orm.exc import NoResultFound
from telegram.ext import CommandHandler

from step_bot.handlers import BaseHandler
from step_bot.models import Chat, Target


class NewTargetHandler(BaseHandler):
    def __init__(self, *args, **kwargs):
        super(NewTargetHandler, self).__init__(*args, **kwargs)

        self.dispatcher.add_handler(CommandHandler('new_target', self.handle, pass_args=True))

    def clean(self, args):
        if len(args) != 1:
            raise ValueError("Number of arguments incorrect")

        return int(args[0])

    def handle(self, bot, update, args):
        try:
            chat_id = update.message.chat_id
            value = self.clean(args)

            db_session = self.get_db()

            current_chat = db_session.query(Chat).filter(Chat.chat_id == str(chat_id)).one()
            new_target = Target(id=uuid.uuid4(), chat=current_chat, name="Новая цель", target_value=value)
            current_chat.current_target = new_target

            db_session.add(new_target)

            db_session.commit()

            bot.send_message(
                chat_id=update.message.chat_id, text=textwrap.dedent("""\
               Для этого чата установлена новая цель!
               
               %s: *%s км*
               """ % (new_target.name, new_target.target_value)), parse_mode=telegram.ParseMode.MARKDOWN)
        except NoResultFound as e:
            bot.send_message(
                chat_id=update.message.chat_id, text=textwrap.dedent("""\
                Ой! Что-то пошло не так, соощите разработчикам!
                """))

            logging.exception(e)
        except ValueError as e:
            bot.send_message(
                chat_id=update.message.chat_id, text=textwrap.dedent("""\
                Неправильно указаны параметры!
                
                Цель устанавливается следующим образом: /new_target <Количество километров>
                """))

            logging.exception(e)


class RenameTargetHandler(BaseHandler):
    def __init__(self, *args, **kwargs):
        super(RenameTargetHandler, self).__init__(*args, **kwargs)

        self.dispatcher.add_handler(CommandHandler('rename_target', self.handle, pass_args=True))

    def clean(self, args):
        if len(args) == 0:
            raise ValueError("Number of arguments incorrect")

        return ' '.join(args)

    def handle(self, bot, update, args):
        db_session = self.get_db()

        try:
            chat_id = update.message.chat_id
            new_name = self.clean(args)

            current_chat = db_session.query(Chat).outerjoin(Chat.current_target)\
                .filter(Chat.chat_id == str(chat_id))\
                .one()

            if current_chat.current_target is None:
                bot.send_message(
                    chat_id=update.message.chat_id, text=textwrap.dedent("""\
                   Похоже что эта группа не имеет цели :( Вначале установите ее!
                   """))
                return

            current_chat.current_target.name = new_name

            bot.send_message(
                chat_id=update.message.chat_id, text=textwrap.dedent("""\
               Наша цель теперь называется: *%s*
               """ % new_name), parse_mode=telegram.ParseMode.MARKDOWN)
        except NoResultFound as e:
            bot.send_message(
                chat_id=update.message.chat_id, text=textwrap.dedent("""\
                Ой! Что-то пошло не так, соощите разработчикам!
                """))
            logging.exception(e)
        except ValueError as e:
            bot.send_message(
                chat_id=update.message.chat_id, text=textwrap.dedent("""\
                Неправильно указаны параметры!

                Цель устанавливается следующим образом: /rename_target <Новое название цели>
                """))
            logging.exception(e)
        finally:
            db_session.commit()


class UpdateTargetHandler(BaseHandler):
    def __init__(self, *args, **kwargs):
        super(UpdateTargetHandler, self).__init__(*args, **kwargs)

        self.dispatcher.add_handler(CommandHandler('update_target', self.handle, pass_args=True))

    def clean(self, args):
        if len(args) != 1:
            raise ValueError("Number of arguments incorrect")

        return int(args)

    def handle(self, bot, update, args):
        db_session = self.get_db()

        try:
            chat_id = update.message.chat_id
            new_value = self.clean(args)

            current_chat = db_session.query(Chat).outerjoin(Chat.current_target)\
                .filter(Chat.chat_id == str(chat_id))\
                .one()

            if current_chat.current_target is None:
                bot.send_message(
                    chat_id=update.message.chat_id, text=textwrap.dedent("""\
                   Похоже что эта группа не имеет цели :( Вначале установите ее!
                   """))
                return

            current_chat.current_target.target_value = new_value

            bot.send_message(
                chat_id=update.message.chat_id, text=textwrap.dedent("""\
               Наша изменилась! Теперь нам необходимо пройти: *%s км*
               """ % new_value), parse_mode=telegram.ParseMode.MARKDOWN)
        except NoResultFound as e:
            bot.send_message(
                chat_id=update.message.chat_id, text=textwrap.dedent("""\
                Ой! Что-то пошло не так, соощите разработчикам!
                """))
            logging.exception(e)
        except ValueError as e:
            bot.send_message(
                chat_id=update.message.chat_id, text=textwrap.dedent("""\
                Неправильно указаны параметры!

                Цель устанавливается следующим образом: /update_target <Новое значение цели>
                """))
            logging.exception(e)
        finally:
            db_session.commit()
