from jumpscale import j

# BE CAREFUL MASTER IS IN: /code/github/rivine/recordchain/Jumpscale9RecordChain/servers/gedis/base/actors/chat.py

JSBASE = j.application.jsbase_get_class()


class chat(JSBASE):
    """
    """

    def __init__(self):
        JSBASE.__init__(self)
        self.chatbot = j.servers.gedis.latest.chatbot

        # check self.chatbot.chatflows for the existing chatflows
        # all required commands are here

    def work_get(self, sessionid, schema_out):
        """
        ```in
        sessionid = "" (S)
        ```
        ```out
        cat = "" (S)
        msg = "" (S)
        error = "" (S)
        options = L(S)
        ```

        """
        res = self.chatbot.session_work_get(sessionid)
        return res

    def work_report(self, sessionid, result):
        """
        ```in
        sessionid = "" (S)
        result = "" (S)
        ```

        ```out
        ```

        """
        self.chatbot.session_work_set(sessionid, result)
        return "hello"

    def session_alive(self, sessionid, schema_out):
        # TODO:*1 check if greenlet is alive
        pass

    def ping(self):
        return 'PONG' 