from flask import render_template, redirect, request, url_for
from blueprints.chat import *
from jumpscale import j
import json

login_manager = j.servers.web.latest.loader.login_manager
chat_server = j.servers.gedis.latest

@blueprint.route('/')
def route_default():
    return redirect('/%s/chat_index.html' % name)

# @login_required
@blueprint.route('/session/<topic>')
def route_chattopic(topic):
    #needs to return the session id
    session_id = j.servers.gedis.latest.chatbot.session_new(topic)
    return render_template("chat_index.html", session_id=session_id)


# @login_required
@blueprint.route('/<template>')
def route_template(template):
    return render_template(template)

@ws_blueprint.route('/ws/gedis')
def echo_socket(socket):
    while not socket.closed:
        message = socket.receive()
        request = message.split(" ")
        cmd, err = chat_server.get_command(request[0])
        if err:
            socket.send(err)
            continue
        res, err = chat_server.process_command(cmd, request)
        if err:
            socket.send(err)
            continue
        socket.send(json.dumps(res))
