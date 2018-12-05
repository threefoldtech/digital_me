from Jumpscale import j


JSBASE = j.application.JSBaseClass


class chatbot(JSBASE):
    """
    """

    def __init__(self):
        JSBASE.__init__(self)
        self.chatbot = j.servers.gedis.latest.chatbot

        # check self.chatbot.chatflows for the existing chatflows
        # all required commands are here

    def work_get(self, sessionid):
        """
        ```in
        sessionid = "" (S)
        ```
        """
        res = self.chatbot.session_work_get(sessionid)
        return j.data.serializers.json.dumps(res)

    def work_report(self, sessionid, result):
        """
        ```in
        sessionid = "" (S)
        result = "" (S)
        ```
        """
        self.chatbot.session_work_set(sessionid, result)
        return

    def session_alive(self, sessionid, schema_out):
        # TODO:*1 check if greenlet is alive
        pass

    def ping(self):
        return 'PONG'

    def session_new(self, topic, schema_out):
        """
        ```in
        topic = ""
        ```
        ```out
        session_id = ""
        ```
        :param topic: Chat bot topic (chatflow file name)
        :param schema_out:
        :return:
        """

        out = schema_out.new()
        out.session_id = j.servers.gedis.latest.chatbot.session_new(topic)
        return out
