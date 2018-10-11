from flask import render_template, redirect, request, make_response
from blueprints.farmercharts import *
from Jumpscale import j
from collections import Counter


# j.tools.threefold_farmer.load(reset=False)


@blueprint.route('/node/<node_id>')
def route_node(node_id):
    node = j.tools.threefold_farmer.bcdb.model_get('threefold.grid.node').get(int(node_id))
    return render_template("node.html", node=node)

@blueprint.route('/')
def route_default():
    nodes = j.tools.threefold_farmer.bcdb.model_get('threefold.grid.node').get_all()
    heatmap_data = Counter((node.location.latitude, node.location.longitude) for node in nodes if node.location.latitude
                           and node.location.longitude)
    max_count = max(heatmap_data.values())
    farmers = j.tools.threefold_farmer.bcdb.model_get('threefold.grid.farmer').get_all()
    countries = {node.location.country for node in nodes}
    return render_template("index.html", nodes=nodes, heatmap_data=heatmap_data, max_count=max_count, farmers=farmers,
                           countries=countries)


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