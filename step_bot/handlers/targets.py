import logging
import textwrap
import uuid

import telegram
from sqlalchemy.orm.exc import NoResultFound

from step_bot.handlers import CommandBaseHandler, CheckTargetMixin
from step_bot.models import Chat, Target


class NewTargetHandler(CommandBaseHandler):
    command = "new_target"
    clean_error_message = "Неправильно указаны параметры!"
    usage_params = "<Количество километров>"

    def clean(self, args):
        if len(args) != 1:
            raise ValueError("Number of arguments incorrect")

        return dict(value=int(args[0]))

    def execute(self, bot, update, cleaned_args):
        db_session = self.get_db()

        try:
            chat_id = update.message.chat_id
            value = cleaned_args.get("value")

            current_chat = db_session.query(Chat).filter(Chat.chat_id == str(chat_id)).one()
            new_target = Target(id=uuid.uuid4(), chat=current_chat, name="Новая цель", target_value=value)
            current_chat.current_target = new_target

            db_session.add(new_target)

            bot.send_message(
                chat_id=update.message.chat_id, text=textwrap.dedent("""\
                Для этого чата установлена новая цель!
               
                %s: *%s км*
                """ % (new_target.name, new_target.target_value)), parse_mode=telegram.ParseMode.MARKDOWN)
        except NoResultFound as e:
            self.send_error(bot, update.message.chat_id)
            logging.exception(e)
        finally:
            db_session.commit()


class RenameTargetHandler(CommandBaseHandler, CheckTargetMixin):
    command = "rename_target"
    clean_error_message = "Неправильно указаны параметры!"
    usage_params = "<Новое название цели>"

    def clean(self, args):
        if len(args) == 0:
            raise ValueError("Number of arguments incorrect")

        return dict(new_name=' '.join(args))

    def execute(self, bot, update, cleaned_args):
        db_session = self.get_db()

        try:
            chat_id = update.message.chat_id
            new_name = cleaned_args.get("new_name")

            current_chat = db_session.query(Chat).outerjoin(Chat.current_target)\
                .filter(Chat.chat_id == str(chat_id))\
                .one()

            if not self.have_target(bot, current_chat):
                return

            current_chat.current_target.name = new_name

            bot.send_message(
                chat_id=update.message.chat_id, text=textwrap.dedent("""\
                Наша цель теперь называется: *%s*
                """ % new_name), parse_mode=telegram.ParseMode.MARKDOWN)
        except NoResultFound as e:
            self.send_error(bot, update.message.chat_id)
            logging.exception(e)
        finally:
            db_session.commit()


class UpdateTargetHandler(CommandBaseHandler, CheckTargetMixin):
    command = "update_target"
    clean_error_message = "Неправильно указаны параметры!"
    usage_params = "<Новое значение цели в километрах>"

    def clean(self, args):
        if len(args) != 1:
            raise ValueError("Number of arguments incorrect")

        return dict(value=int(args[0]))

    def execute(self, bot, update, cleaned_args):
        db_session = self.get_db()

        try:
            chat_id = update.message.chat_id
            new_value = cleaned_args.get("value")

            current_chat = db_session.query(Chat).outerjoin(Chat.current_target)\
                .filter(Chat.chat_id == str(chat_id))\
                .one()

            if not self.have_target(bot, current_chat):
                return

            current_chat.current_target.target_value = new_value

            bot.send_message(
                chat_id=update.message.chat_id, text=textwrap.dedent("""\
                Наша изменилась! Теперь нам необходимо пройти: *%s км*
                """ % new_value), parse_mode=telegram.ParseMode.MARKDOWN)
        except NoResultFound as e:
            self.send_error(bot, update.message.chat_id)
            logging.exception(e)
        finally:
            db_session.commit()
