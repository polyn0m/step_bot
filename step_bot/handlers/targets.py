import logging
import textwrap
import uuid
from datetime import datetime

import telegram
from sqlalchemy.orm.exc import NoResultFound

from step_bot.handlers import CommandBaseHandler, CheckTargetMixin
from step_bot.models import Chat, Target


class NewTargetHandler(CommandBaseHandler):
    command = "new_target"
    clean_error_message = "Неправильно указаны параметры!"
    usage_params = "<Количество километров> <Дата окончания цели>"

    def clean(self, args):
        if len(args) != 2:
            raise ValueError("Number of arguments incorrect")

        return dict(value=int(args[0]), end=datetime.strptime(args[1], "%d.%m.%Y"))

    def execute(self, bot, update, cleaned_args):
        db_session = self.get_db()

        try:
            chat_id = update.message.chat_id
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
                )), parse_mode=telegram.ParseMode.MARKDOWN)
        except NoResultFound as e:
            self.send_error(bot, update.message.chat_id)
            logging.exception(e)
        finally:
            db_session.commit()


class UpdateTargetHandler(CommandBaseHandler, CheckTargetMixin):
    command = "update_target"
    clean_error_message = "Неправильно указаны параметры!"
    usage_params = "<Действие=name,date,value> <Значение=строка,дата,число>"

    def clean(self, args):
        if len(args) < 2:
            raise ValueError("Number of arguments incorrect")

        action = args[0]
        if action not in ["value", "date", "name"]:
            raise ValueError("Not allowed action")

        if action == "value":
            value = int(args[1])
        elif action == "date":
            value = datetime.strptime(args[1], "%d.%m.%Y")
        elif action == "name":
            value = " ".join(args[1:])
        else:
            raise LookupError

        return dict(action=action, value=value)

    def execute(self, bot, update, cleaned_args):
        db_session = self.get_db()

        try:
            chat_id = update.message.chat_id
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
                    chat_id=update.message.chat_id, text=textwrap.dedent("""\
                    Наша цель изменилась! Теперь нам необходимо пройти *%s км*
                    """ % new_value), parse_mode=telegram.ParseMode.MARKDOWN)
            elif action == "date":
                current_chat.current_target.target_date = new_value

                bot.send_message(
                    chat_id=update.message.chat_id, text=textwrap.dedent("""\
                    Теперь наша цель заканчивается *%s*
                    """ % new_value.strftime("%d.%m.%Y")), parse_mode=telegram.ParseMode.MARKDOWN)
            elif action == "name":
                current_chat.current_target.name = new_value

                bot.send_message(
                    chat_id=update.message.chat_id, text=textwrap.dedent("""\
                    Теперь наша цель называется *%s*
                    """ % new_value), parse_mode=telegram.ParseMode.MARKDOWN)
        except NoResultFound as e:
            self.send_error(bot, update.message.chat_id)
            logging.exception(e)
        finally:
            db_session.commit()
