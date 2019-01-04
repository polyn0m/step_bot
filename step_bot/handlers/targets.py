import logging
import textwrap
import uuid
from datetime import datetime

import telegram
from sqlalchemy.orm.exc import NoResultFound

from step_bot.handlers import CommandBaseHandler, CheckTargetMixin, restricted
from step_bot.models import Chat, Target


class NewTargetHandler(CommandBaseHandler):
    command = "new_target"
    clean_error_message = "Неправильно указаны параметры!"
    usage_params = "<Количество километров> <Дата окончания цели>"

    def clean_args(self, args):
        if len(args) != 2:
            raise ValueError("Number of arguments incorrect")
        end_date = datetime.strptime(args[1], "%d.%m.%Y").replace(tzinfo=self.settings.BOT_TZ).date()
        if end_date < datetime.now(tz=self.settings.BOT_TZ).date():
            raise ValueError("End date must greater than now!")

        return dict(value=int(args[0]), end=end_date)

    @restricted
    def execute(self, bot, update, cleaned_args):
        chat_id = update.effective_chat.id

        db_session = self.get_db()

        try:
            value = cleaned_args.get("value")
            end_date = cleaned_args.get("end")

            current_chat = db_session.query(Chat).filter(Chat.chat_id == str(chat_id)).one()
            new_target = Target(
                id=uuid.uuid4(), chat=current_chat, name="Новая цель", target_date=end_date, target_value=value * 1000
            )

            current_chat.current_target_id = new_target.id
            current_chat.current_target = new_target

            db_session.add(new_target)

            bot.send_message(
                chat_id=update.message.chat_id, text=textwrap.dedent("""\
                Для этого чата установлена новая цель!
               
                *{0}* в *{1} км* к *{2}*
                """.format(
                    new_target.name,
                    new_target.target_value / 1000,
                    new_target.target_date.strftime("%d.%m.%Y")
                )), reply_to_message_id=update.effective_message.message_id, parse_mode=telegram.ParseMode.MARKDOWN)
        except NoResultFound as e:
            self.send_error(bot, chat_id, reply_to_message_id=update.effective_message.message_id)

            logging.exception(e)
        finally:
            db_session.commit()


class UpdateTargetHandler(CommandBaseHandler, CheckTargetMixin):
    command = "update_target"
    clean_error_message = "Неправильно указаны параметры!"
    usage_params = "<Действие=name,date,initial,value> <Значение=строка,дата,число,число>"

    def clean_args(self, args):
        if len(args) < 2:
            raise ValueError("Number of arguments incorrect")

        action = args[0]
        if action not in ["value", "initial", "date", "name"]:
            raise ValueError("Not allowed action")

        if action == "value" or action == "initial":
            value = int(args[1])
        elif action == "date":
            value = datetime.strptime(args[1], "%d.%m.%Y").replace(tzinfo=self.settings.BOT_TZ).date()
        elif action == "name":
            value = " ".join(args[1:])
        else:
            raise LookupError

        return dict(action=action, value=value)

    @restricted
    def execute(self, bot, update, cleaned_args):
        chat_id = update.effective_chat.id

        db_session = self.get_db()

        try:
            action = cleaned_args.get("action")
            new_value = cleaned_args.get("value")

            current_chat = db_session.query(Chat).outerjoin(Chat.current_target)\
                .filter(Chat.chat_id == str(chat_id))\
                .one()

            if not self.have_target(bot, current_chat):
                return

            if action == "value":
                current_chat.current_target.target_value = new_value * 1000

                bot.send_message(
                    chat_id=chat_id, text=textwrap.dedent("""\
                    Наша цель изменилась! Теперь нам необходимо пройти *{0} км*
                    """.format(new_value)),
                    reply_to_message_id=update.effective_message.message_id, parse_mode=telegram.ParseMode.MARKDOWN)
            elif action == "initial":
                current_chat.current_target.initial_value = new_value

                bot.send_message(
                    chat_id=chat_id, text=textwrap.dedent("""\
                    Наша цель изменилась! Начальное значение шагов стало равняться *{0}*
                    """.format(new_value)),
                    reply_to_message_id=update.effective_message.message_id, parse_mode=telegram.ParseMode.MARKDOWN)
            elif action == "date":
                current_chat.current_target.target_date = new_value

                bot.send_message(
                    chat_id=chat_id, text=textwrap.dedent("""\
                    Теперь наша цель заканчивается *{0}*
                    """.format(new_value.strftime("%d.%m.%Y"))),
                    reply_to_message_id=update.effective_message.message_id, parse_mode=telegram.ParseMode.MARKDOWN)
            elif action == "name":
                current_chat.current_target.name = new_value

                bot.send_message(
                    chat_id=chat_id, text=textwrap.dedent("""\
                    Теперь наша цель называется *{0}*
                    """.format(new_value)),
                    reply_to_message_id=update.effective_message.message_id, parse_mode=telegram.ParseMode.MARKDOWN)
        except NoResultFound as e:
            self.send_error(bot, chat_id, reply_to_message_id=update.effective_message.message_id)

            logging.exception(e)
        finally:
            db_session.commit()
