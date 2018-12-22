import logging
import textwrap
import uuid
from datetime import datetime

import telegram
from sqlalchemy import func
from sqlalchemy.orm.exc import NoResultFound

from step_bot.handlers import CommandBaseHandler, CheckTargetMixin
from step_bot.models import Chat, Step


class StepCalculateMixin:
    def recalculate_steps(self, db_session, chat):
        sum = db_session.query(func.sum(Step.steps).label('total_steps'))\
            .filter(Step.target == chat.current_target)\
            .group_by(Step.target_id)\
            .one()

        chat.current_target.current_value = sum.total_steps


class TodayHandler(CommandBaseHandler, CheckTargetMixin, StepCalculateMixin):
    command = "today"
    clean_error_message = "Указано не верное количество шагов!"
    usage_params = "<Число шагов>"

    def clean(self, args):
        if len(args) != 1:
            raise ValueError("Number of arguments incorrect")
        value = int(args[0])
        if value < 0:
            raise ValueError("Steps must greater than 0")

        return dict(value=value)

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

            self.recalculate_steps(db_session, current_chat)
        except NoResultFound as e:
            self.send_error(bot, update.message.chat_id)
            logging.exception(e)
        finally:
            db_session.commit()


class DayHandler(CommandBaseHandler, CheckTargetMixin, StepCalculateMixin):
    command = "day"
    clean_error_message = "Неправильно указаны параметры!"
    usage_params = "<Дата ДД.ММ.ГГГГ> <Число шагов>"

    def clean(self, args):
        if len(args) != 2:
            raise ValueError("Number of arguments incorrect")
        value = int(args[1])
        if value < 0:
            raise ValueError("Steps must greater than 0")

        return dict(date=datetime.strptime(args[0], "%d.%m.%Y"), value=value)

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

            self.recalculate_steps(db_session, current_chat)
        except NoResultFound as e:
            self.send_error(bot, update.message.chat_id)
            logging.exception(e)
        finally:
            db_session.commit()
