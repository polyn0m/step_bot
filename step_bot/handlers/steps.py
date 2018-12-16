import logging
import textwrap
from datetime import datetime

from sqlalchemy.orm.exc import NoResultFound
from telegram.ext import CommandHandler

from step_bot.handlers import CommandBaseHandler, CheckTargetMixin
from step_bot.models import Chat


class TodayHandler(CommandBaseHandler, CheckTargetMixin):
    command = "today"
    clean_error_message = "Указано не верное количество шагов!"
    usage_params = "<Число шагов>"

    def clean(self, args):
        if len(args) != 1:
            raise ValueError("Number of arguments incorrect")

        return dict(value=int(args[0]))

    def execute(self, bot, update, cleaned_args):
        db_session = self.get_db()

        try:
            chat_id = update.message.chat_id
            steps = cleaned_args.get("value")

            current_chat = db_session.query(Chat).outerjoin(Chat.current_target) \
                .filter(Chat.chat_id == str(chat_id)) \
                .one()

            if not self.have_target(bot, current_chat):
                return

            # TODO
        except NoResultFound as e:
            self.send_error(bot, update.message.chat_id)
            logging.exception(e)
        finally:
            db_session.commit()


class DayHandler(CommandBaseHandler):
    command = "day"
    clean_error_message = "Неправильно указаны параметры!"

    def clean(self, args):
        if len(args) != 2:
            raise ValueError("Number of arguments incorrect")

        return dict(date=datetime.strptime(args[0], "%d-%m-%Y"), value=int(args[1]))

    def execute(self, bot, update, cleaned_args):
        pass
