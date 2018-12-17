from Jumpscale import j

JSBASE = j.application.JSBaseClass


class chatbot(JSBASE):
    """
    Chat bot gedis actor class
    """

    def __init__(self):
        JSBASE.__init__(self)
        self.chatbot = j.servers.gedis.latest.chatbot
        return

    def work_get(self, session_id):
        """
        ```in
        session_id = "" (S)
        ```
        command responsible for getting new questions from chatbot session questions queue
        :param session_id: User's session id to be identified by server
        :return
        """
        res = self.chatbot.session_work_get(session_id)
        return j.data.serializers.json.dumps(res)

    def work_report(self, session_id, result):
        """
        command responsible for setting answers into chatbot session answers queue
        ```in
        session_id = "" (S)
        result = "" (S)
        ```
        """
        self.chatbot.session_work_set(session_id, result)
        return

    def session_new(self, topic, schema_out):
        """
        ```in
        topic = ""
        ```
        ```out
        session_id = ""
        ```
        starts a new session for the specified topic
        :param topic: Chat bot topic (chatflow file name)
        :param schema_out:
        :return: the new session id
        """
        out = schema_out.new()
        out.session_id = j.servers.gedis.latest.chatbot.session_new(topic)
        return out
