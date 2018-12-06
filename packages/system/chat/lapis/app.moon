lapis = require "lapis"

class extends lapis.Application
    @enable "etlua"
    "/:topic": =>
        req = @req.parsed_url
        scheme = "ws"
        if req.scheme == "https"
            scheme = "wss"
        @url = scheme .. "://" .. req.host .. ":" .. req.port
        @topic = @params.topic
        render: "chat.chat"
