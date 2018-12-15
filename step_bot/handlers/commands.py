from step_bot.handlers import BaseHandler


class SetTargetHandler(BaseHandler):
    def __init__(self, *args, **kwargs):
        super(SetTargetHandler, self).__init__(*args, **kwargs)
