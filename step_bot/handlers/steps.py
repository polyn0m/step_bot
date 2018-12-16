import logging
import textwrap
import uuid
from datetime import datetime

import telegram
from sqlalchemy.orm.exc import NoResultFound

from step_bot.handlers import CommandBaseHandler, CheckTargetMixin
from step_bot.models import Chat, Step


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
            user_id = update.message.from_user.id
            steps = cleaned_args.get("value")
            today = datetime.today().date()

            current_chat = db_session.query(Chat).outerjoin(Chat.current_target) \
                .filter(Chat.chat_id == str(chat_id)) \
                .one()

            if not self.have_target(bot, current_chat):
                return

            try:
                step_info = db_session.query(Step) \
                    .filter(Step.user_id == str(user_id), Step.date == today) \
                    .one()

                prev_value = step_info.steps

                step_info.steps = steps

                bot.send_message(
                    chat_id=update.message.chat_id, text=textwrap.dedent("""\
                    %s, твои шаги за сегодня обновлены! Сегодня (%s) ты прошел(а) *%s* шагов, вместо _%s_ шагов!
                    """ % (update.message.from_user.first_name, today.strftime("%d.%m.%Y"), steps, prev_value)),
                    parse_mode=telegram.ParseMode.MARKDOWN
                )
            except NoResultFound:
                step_info = Step(
                    id=uuid.uuid4(), user_id=user_id,
                    target=current_chat.current_target,
                    date=today, steps=steps
                )

                db_session.add(step_info)

                bot.send_message(
                    chat_id=update.message.chat_id, text=textwrap.dedent("""\
                    %s! Сегодня (%s) ты прошел(а) *%s* шагов! Молодец!
                    """ % (update.message.from_user.first_name, today.strftime("%d.%m.%Y"), steps)),
                    parse_mode=telegram.ParseMode.MARKDOWN
                )
        except NoResultFound as e:
            self.send_error(bot, update.message.chat_id)
            logging.exception(e)
        finally:
            db_session.commit()


class DayHandler(CommandBaseHandler, CheckTargetMixin):
    command = "day"
    clean_error_message = "Неправильно указаны параметры!"
    usage_params = "<Дата ДД.ММ.ГГГГ> <Число шагов>"

    def clean(self, args):
        if len(args) != 2:
            raise ValueError("Number of arguments incorrect")

        return dict(date=datetime.strptime(args[0], "%d.%m.%Y"), value=int(args[1]))

    def execute(self, bot, update, cleaned_args):
        db_session = self.get_db()

        try:
            chat_id = update.message.chat_id
            user_id = update.message.from_user.id

            steps = cleaned_args.get("value")
            day = cleaned_args.get("date")

            current_chat = db_session.query(Chat).outerjoin(Chat.current_target) \
                .filter(Chat.chat_id == str(chat_id)) \
                .one()

            if not self.have_target(bot, current_chat):
                return

            try:
                step_info = db_session.query(Step) \
                    .filter(Step.user_id == str(user_id), Step.date == day) \
                    .one()

                prev_value = step_info.steps

                step_info.steps = steps

                bot.send_message(
                    chat_id=update.message.chat_id, text=textwrap.dedent("""\
                            %s, твои шаги обновлены! %s ты прошел(а) *%s* шагов, вместо _%s_ шагов!
                            """ % (update.message.from_user.first_name, day.strftime("%d.%m.%Y"), steps, prev_value)),
                    parse_mode=telegram.ParseMode.MARKDOWN
                )
            except NoResultFound:
                step_info = Step(
                    id=uuid.uuid4(), user_id=user_id,
                    target=current_chat.current_target,
                    date=day, steps=steps
                )

                db_session.add(step_info)

                bot.send_message(
                    chat_id=update.message.chat_id, text=textwrap.dedent("""\
                            %s! %s ты прошел(а) *%s* шагов! Молодец!
                            """ % (update.message.from_user.first_name, day.strftime("%d.%m.%Y"), steps)),
                    parse_mode=telegram.ParseMode.MARKDOWN
                )
        except NoResultFound as e:
            self.send_error(bot, update.message.chat_id)
            logging.exception(e)
        finally:
            db_session.commit()
