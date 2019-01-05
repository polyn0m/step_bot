import logging
import textwrap
import uuid
from datetime import datetime

import telegram
from sqlalchemy import func
from sqlalchemy.orm.exc import NoResultFound
from telegram import ForceReply
from telegram.ext import CommandHandler, MessageHandler, ConversationHandler, Filters

from step_bot.handlers import CheckTargetMixin, ConversationBaseHandler
from step_bot.models import Chat, Step


class StepCalculateMixin:
    def recalculate_steps(self, db_session, chat):
        sum = db_session.query(func.sum(Step.steps).label('total_steps')) \
            .filter(Step.target == chat.current_target) \
            .group_by(Step.target_id) \
            .one()

        chat.current_target.current_value = chat.current_target.initial_value + sum.total_steps


class TodayHandler(ConversationBaseHandler, CheckTargetMixin, StepCalculateMixin):
    INPUT_STEPS = 'input_steps'

    def __init__(self, *args, **kwargs):
        self.entry_points = [
            CommandHandler('today', self.start)
        ]
        self.states = {
            TodayHandler.INPUT_STEPS: [MessageHandler(Filters.text, self.input_steps)]
        }

        super(TodayHandler, self).__init__(*args, **kwargs)

    def clean_steps(self, text):
        value = int(text)
        if value < 0:
            raise ValueError("Steps must greater than 0")

        return value

    def start(self, bot, update):
        today = datetime.now(tz=self.settings.BOT_TZ).date()

        bot.send_message(
            chat_id=update.effective_chat.id, text=textwrap.dedent("""\
            *{0}*, привет! Сколько шагов ты прошел за *{1}*?
            """.format(update.message.from_user.first_name, today.strftime("%d.%m.%Y"))),
            reply_to_message_id=update.effective_message.message_id, reply_markup=ForceReply(selective=True),
            parse_mode=telegram.ParseMode.MARKDOWN
        )

        return TodayHandler.INPUT_STEPS

    def input_steps(self, bot, update):
        chat_id = update.effective_chat.id
        user_id = update.effective_user.id

        db_session = self.get_db()

        try:
            steps = self.clean_steps(update.effective_message.text)
            today = datetime.now(tz=self.settings.BOT_TZ).date()

            current_chat = db_session.query(Chat).outerjoin(Chat.current_target) \
                .filter(Chat.chat_id == str(chat_id)) \
                .one()

            if not self.have_target(bot, current_chat):
                return

            try:
                step_info = db_session.query(Step) \
                    .filter(
                        Step.target == current_chat.current_target,
                        Step.user_id == str(user_id),
                        Step.date == today) \
                    .one()

                prev_value = step_info.steps

                step_info.steps = steps

                bot.send_message(
                    chat_id=chat_id, text=textwrap.dedent("""\
                    *{0}*, твои шаги за сегодня обновлены! Сегодня (*{1}*) ты прошел(а) *{2}* шагов, вместо _{3}_ шагов!
                    """.format(update.effective_user.first_name, today.strftime("%d.%m.%Y"), steps, prev_value)),
                    reply_to_message_id=update.effective_message.message_id, parse_mode=telegram.ParseMode.MARKDOWN
                )
            except NoResultFound:
                step_info = Step(
                    id=uuid.uuid4(), user_id=user_id,
                    target=current_chat.current_target,
                    date=today, steps=steps
                )

                db_session.add(step_info)

                bot.send_message(
                    chat_id=chat_id, text=textwrap.dedent("""\
                    *{0}*! *{1}* ты прошел(а) *{2}* шагов! Молодец!
                    """.format(update.effective_user.first_name, today.strftime("%d.%m.%Y"), steps)),
                    reply_to_message_id=update.effective_message.message_id, parse_mode=telegram.ParseMode.MARKDOWN
                )

            self.recalculate_steps(db_session, current_chat)

            return ConversationHandler.END
        except NoResultFound as e:
            self.send_error(bot, chat_id)
            logging.exception(e)
        except ValueError as e:
            self.send_clean_error(
                bot, chat_id, "Указано не верное количество шагов, напиши количество шагов в виде числа!",
                reply_to_message_id=update.effective_message.message_id, reply_markup=ForceReply(selective=True)
            )

            logging.exception(e)
        finally:
            db_session.commit()


class DayHandler(ConversationBaseHandler, CheckTargetMixin, StepCalculateMixin):
    INPUT_DATE = 'input_date'
    INPUT_STEPS = 'input_steps'

    conversation_data = dict()

    def __init__(self, *args, **kwargs):
        self.entry_points = [
            CommandHandler('day', self.start)
        ]
        self.states = {
            DayHandler.INPUT_DATE: [MessageHandler(Filters.text, self.input_date)],
            DayHandler.INPUT_STEPS: [MessageHandler(Filters.text, self.input_steps)]
        }

        super(DayHandler, self).__init__(*args, **kwargs)

    def clean_date(self, text):
        value = datetime.strptime(text, "%d.%m.%Y").replace(tzinfo=self.settings.BOT_TZ).date()

        return value

    def clean_steps(self, text):
        value = int(text)
        if value < 0:
            raise ValueError("Steps must greater than 0")

        return value

    def start(self, bot, update):
        bot.send_message(
            chat_id=update.effective_chat.id, text=textwrap.dedent("""\
            *{0}*, привет! За какой день ты хочешь указать шаги?
            """.format(update.effective_user.first_name)),
            reply_to_message_id=update.effective_message.message_id, reply_markup=ForceReply(selective=True),
            parse_mode=telegram.ParseMode.MARKDOWN
        )

        return DayHandler.INPUT_DATE

    def input_date(self, bot, update):
        chat_id = update.effective_chat.id

        db_session = self.get_db()

        try:
            day = self.clean_date(update.effective_message.text)
            today = datetime.now(tz=self.settings.BOT_TZ).date()

            current_chat = db_session.query(Chat).outerjoin(Chat.current_target) \
                .filter(Chat.chat_id == str(chat_id)) \
                .one()

            if not self.have_target(bot, current_chat):
                return

            if day < current_chat.current_target.date_creation.date():
                bot.send_message(
                    chat_id=update.message.chat_id, text=textwrap.dedent("""\
                    *{0}*, дата для шагов не может быть раньше чем дата начала (*{1}*) у цели!
                    """.format(
                        update.message.from_user.first_name,
                        current_chat.current_target.date_creation.strftime("%d.%m.%Y"))
                    ), reply_to_message_id=update.effective_message.message_id, reply_markup=ForceReply(selective=True),
                    parse_mode=telegram.ParseMode.MARKDOWN
                )
                return
            if day > today:
                bot.send_message(
                    chat_id=update.message.chat_id, text=textwrap.dedent("""\
                    *{0}*, дата для шагов не может быть больше чем сегодня! Читер!
                    """.format(update.message.from_user.first_name)
                    ), reply_to_message_id=update.effective_message.message_id, reply_markup=ForceReply(selective=True),
                    parse_mode=telegram.ParseMode.MARKDOWN
                )
                return

            self.conversation_data[self.handler.current_conversation] = day

            bot.send_message(
                chat_id=update.effective_chat.id, text=textwrap.dedent("""\
                *{0}*, понял! А сколько шагов пройдено за *{1}*?
                """.format(update.effective_user.first_name, day.strftime("%d.%m.%Y"))),
                reply_to_message_id=update.effective_message.message_id, reply_markup=ForceReply(selective=True),
                parse_mode=telegram.ParseMode.MARKDOWN
            )

            return DayHandler.INPUT_STEPS
        except ValueError as e:
            self.send_clean_error(
                bot, chat_id, "Я не понимаю что ты указал(а), мне понятны даты в виде ДД.ММ.ГГГГ!",
                reply_to_message_id=update.effective_message.message_id
            )

            logging.exception(e)
        except NoResultFound as e:
            self.send_error(bot, update.message.chat_id)
            logging.exception(e)

    def input_steps(self, bot, update):
        chat_id = update.effective_chat.id
        user_id = update.effective_user.id

        db_session = self.get_db()

        try:
            steps = self.clean_steps(update.effective_message.text)
            day = self.conversation_data[self.handler.current_conversation]

            current_chat = db_session.query(Chat).outerjoin(Chat.current_target) \
                .filter(Chat.chat_id == str(chat_id)) \
                .one()

            if not self.have_target(bot, current_chat):
                return

            try:
                step_info = db_session.query(Step) \
                    .filter(
                        Step.target == current_chat.current_target,
                        Step.user_id == str(user_id),
                        Step.date == day) \
                    .one()

                prev_value = step_info.steps

                step_info.steps = steps

                bot.send_message(
                    chat_id=update.message.chat_id, text=textwrap.dedent("""\
                    *{0}*, твои шаги обновлены! *{1}* ты прошел(а) *{2}* шагов, вместо _{3}_ шагов!
                    """.format(
                        update.message.from_user.first_name, day.strftime("%d.%m.%Y"), steps, prev_value
                    )),
                    reply_to_message_id=update.effective_message.message_id, parse_mode=telegram.ParseMode.MARKDOWN
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
                    *{0}*! *{1}* ты прошел(а) *{2}* шагов! Молодец!
                    """.format(update.message.from_user.first_name, day.strftime("%d.%m.%Y"), steps)),
                    reply_to_message_id=update.effective_message.message_id, parse_mode=telegram.ParseMode.MARKDOWN
                )

            self.recalculate_steps(db_session, current_chat)

            del self.conversation_data[self.handler.current_conversation]

            return ConversationHandler.END
        except NoResultFound as e:
            self.send_error(bot, update.message.chat_id)
            logging.exception(e)
        finally:
            db_session.commit()
