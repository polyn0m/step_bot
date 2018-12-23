import logging
import textwrap

from telegram.ext import CommandHandler


def init_handlers(dispatcher, db, settings):
    from step_bot.handlers.steps import TodayHandler, DayHandler
    from step_bot.handlers.targets import NewTargetHandler, UpdateTargetHandler
    from step_bot.handlers.greetings import GroupHandler, P2PEchoHandler
    from step_bot.handlers.stats import StatHandler

    handlers = set()

    options = dict(dispatcher=dispatcher, db=db, settings=settings)

    handlers.add(P2PEchoHandler(**options))

    handlers.add(GroupHandler(**options))

    handlers.add(NewTargetHandler(**options))
    handlers.add(UpdateTargetHandler(**options))

    handlers.add(TodayHandler(**options))
    handlers.add(DayHandler(**options))

    handlers.add(StatHandler(**options))

    return handlers


def restricted(handler):

    def wrapped(self, bot, update, cleaned_args, *args, **kwargs):
        if not isinstance(self, CommandBaseHandler):
            logging.error("restricted decorator can use only with commands!")
            return

        from_user_id = update.message.from_user.id
        admins = update.effective_chat.get_administrators()

        is_admin = any(admin for admin in admins if admin.user.id == from_user_id)

        if is_admin or update.effective_chat.all_members_are_administrators is not None:
            return handler(self, bot, update, cleaned_args, *args, **kwargs)
        else:
            bot.send_message(
                chat_id=update.message.chat_id, text="Управлять мной может только администратор группы!"
            )

    return wrapped


class BaseHandler:
    dispatcher = None
    get_db = None

    settings = None

    def __init__(self, dispatcher, db, settings):
        self.dispatcher = dispatcher
        self.get_db = db

        self.settings = settings

    def send_error(self, bot, chat_id):
        bot.send_message(chat_id=chat_id, text="Ой! Что-то пошло не так, соощите разработчикам!")


class CommandBaseHandler(BaseHandler):
    command = None

    clean_error_message = ''
    usage_params = ''

    def __init__(self, *args, **kwargs):
        super(CommandBaseHandler, self).__init__(*args, **kwargs)

        self.dispatcher.add_handler(CommandHandler(self.command, self.handle, pass_args=True))

    def clean(self, args):
        raise NotImplemented

    def send_clean_error(self, bot, chat_id, e):
        bot.send_message(
            chat_id=chat_id, text=textwrap.dedent("""\
            {0}

            Использование: /{1} {2}
            """.format(self.clean_error_message, self.command, self.usage_params)))

    def handle(self, bot, update, args):
        try:
            cleaned_args = self.clean(args)

            self.execute(bot, update, cleaned_args)
        except ValueError as e:
            self.send_clean_error(bot, update.message.chat_id, e)
            logging.exception(e)

    def execute(self, bot, update, cleaned_args):
        raise NotImplemented


class CheckTargetMixin:
    def __send_no_target(self, bot, chat_id):
        bot.send_message(chat_id=chat_id, text="Похоже что эта группа не имеет цели :( Вначале установите ее!")

    def have_target(self, bot, chat):
        if chat.current_target is None:
            self.__send_no_target(bot, chat.chat_id)

            return False
        return True
