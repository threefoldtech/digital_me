from Jumpscale import j
import gevent
import sys
from importlib import import_module

JSBASE = j.application.JSBaseClass


class GedisChatBotFactory(JSBASE):
    def __init__(self,ws):
        JSBASE.__init__(self)
        self.ws = ws
        self.sessions = {}  # open chatsessions
        self.chat_flows = {}  # are the flows to run, code being executed to talk with user
        # self.chatflows_load()
        self.sessions_id_latest = 0

    def session_new(self, topic, **kwargs):
        """
        returns the last session id
        """
        self.sessions_id_latest += 1
        topic_method = self.chat_flows[topic]
        bot = GedisChatBotSession(self.sessions_id_latest, topic_method, **kwargs)
        self.sessions[str(self.sessions_id_latest)] = bot
        return self.sessions_id_latest

    def session_work_get(self, sessionid):
        bot = self.sessions[sessionid]
        return bot.q_out.get(block=True)

    def session_work_set(self, sessionid, val):
        bot = self.sessions[sessionid]
        return bot.q_in.put(val)

    def chatflows_load(self, chatflows_dir):
        """
        look for the chat flows exist in chatflow_dir to load them all under self.chat_flows
        """
        for chatflow in j.sal.fs.listFilesInDir(chatflows_dir, recursive=True, filter="*.py", followSymlinks=True):
            dpath = j.sal.fs.getDirName(chatflow)
            if dpath not in sys.path:
                sys.path.append(dpath)
            self._logger.info("chat:%s" % chatflow)
            modulename = j.sal.fs.getBaseName(chatflow)[:-3]
            if modulename.startswith("_"):
                continue
            loaded_module = import_module(modulename)
            self.chat_flows[modulename] = loaded_module.chat

    def test(self):
        gevent.spawn(test, factory=self)
        gevent.sleep(100)


class GedisChatBotSession(JSBASE):
    def __init__(self, sessionid, topic_method, **kwargs):
        JSBASE.__init__(self)
        self.sessionid = sessionid
        self.q_out = gevent.queue.Queue()  # to browser
        self.q_in = gevent.queue.Queue()  # from browser
        self.greenlet = gevent.spawn(topic_method, bot=self)
        self.kwargs = kwargs

    def string_ask(self, msg, **kwargs):
        self.q_out.put({
            "cat": "string_ask",
            "msg": msg,
            "kwargs": kwargs
        })
        return self.q_in.get()

    def password_ask(self, msg, **kwargs):
        self.q_out.put({
            "cat": "password_ask",
            "msg": msg,
            "kwargs": kwargs
        })
        return self.q_in.get()

    def text_ask(self, msg, **kwargs):
        self.q_out.put({
            "cat": "text_ask",
            "msg": msg,
            "kwargs": kwargs
        })
        return self.q_in.get()

    def int_ask(self, msg, **kwargs):
        self.q_out.put({
            "cat": "int_ask",
            "msg": msg,
            "kwargs": kwargs
        })
        return self.q_in.get()

    def md_show(self, msg, **kwargs):
        self.q_out.put({
            "cat": "md_show",
            "msg": msg,
            "kwargs": kwargs
        })
        return self.q_in.get()

    def redirect(self, msg, **kwargs):
        self.q_out.put({
            "cat": "redirect",
            "msg": msg,
            "kwargs": kwargs
        })

    def multi_choice(self, msg, options, **kwargs):
        self.q_out.put({
            "cat": "multi_choice",
            "msg": msg,
            "options": options,
            "kwargs": kwargs
        })
        return self.q_in.get()

    def single_choice(self, msg, options, **kwargs):
        self.q_out.put({
            "cat": "single_choice",
            "msg": msg,
            "options": options,
            "kwargs": kwargs
        })
        return self.q_in.get()

    def drop_down_choice(self, msg, options, **kwargs):
        self.q_out.put({
            "cat": "drop_down_choice",
            "msg": msg,
            "options": options,
            "kwargs": kwargs
        })
        return self.q_in.get()


def test(factory):
    sid = "123"
    factory.session_new("test_chat")
    nr = 0
    while True:
        factory.session_work_get(sid)
        gevent.sleep(1)  # browser is doing something
        nr += 1
        factory.session_work_set(sid, nr)
