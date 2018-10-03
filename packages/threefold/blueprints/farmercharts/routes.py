from flask import render_template, redirect, request, make_response
from blueprints.farmercharts import *
from Jumpscale import j




@blueprint.route('/node/<node_id>')
def route_default(node_id):
    node = j.tools.threefold_farmer.bcdb.model_get('threefold.grid.node').get(int(node_id))
    return render_template("node.html", node=node)



@blueprint.route('/jsclient.js')
def load_js_client():
    scheme = "ws"
    if request.scheme == "https":
        scheme = "wss"
    js_code = j.servers.gedis.latest.code_js_client
    js_client = js_code.replace("%%host%%", "{scheme}://{host}/chat/ws/gedis".format(scheme=scheme, host=request.host))
    res = make_response(js_client)
    res.headers['content-type'] = "application/javascript"
    return res

@ws_blueprint.route('/ws/gedis')
def chat_interact(socket):
    while not socket.closed:
        j.servers.gedis.latest.handler.handle_websocket(socket=socket,namespace="base")