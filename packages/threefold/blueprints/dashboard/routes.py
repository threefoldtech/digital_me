from flask import render_template, redirect, request, make_response
from blueprints.dashboard import *
from Jumpscale import j
from collections import Counter
import pycountry

# j.tools.threefold_farmer.load(reset=False)
client = j.servers.gedis.latest.client_get()
node_model = j.tools.threefold_farmer.bcdb.model_get('threefold.grid.node')


@blueprint.route('/node/<node_id>')
def route_node(node_id):
    node = j.tools.threefold_farmer.bcdb.model_get('threefold.grid.node').get(int(node_id))
    return render_template("node/node.html", node=node)

@blueprint.route('/', methods=['GET'])
def route_default():
    search_input = request.args.to_dict()
    # j.shell()
    nodes = client.farmer.node_find(**search_input).res
    capacity_totals = calculate_capacities(nodes)
    # j.shell()
    heatmap_data = list({'latLng':[node.location.latitude, node.location.longitude],'name':node.location.country} for node in nodes if node.location.latitude
                           and node.location.longitude)
    
    # if heatmap_data:
    #     max_count = max(heatmap_data.values())
    # else:
    #     max_count = 0
    max_count = 0
    heatmap_data = j.data.serializers.json.dumps(heatmap_data)
    country_codes = list(pycountry.countries.get(name=node.location.country).alpha_2 for node in nodes if node.location.latitude and node.location.longitude)
    farmers = client.farmer.farmers_get().res
    countries = {node.location.country for node in nodes}
    return render_template("dashboard/index.html", nodes=nodes, heatmap_data=heatmap_data, country_codes = country_codes, max_count=max_count, farmers=farmers,
                           countries=countries,totals = capacity_totals)

def calculate_capacities(nodes):
    totals = {'nodes_up':0,'nodes_down':0,'total_capacities':{'cru':0,'hru':0,'mru':0,'sru':0},'reserved_capacities':{'cru':0,'hru':0,'mru':0,'sru':0},'used_capacities':{'cru':0,'hru':0,'mru':0,'sru':0}}
    for node in nodes:
        totals['total_capacities']['cru'] += node.capacity_total.cru
        totals['total_capacities']['hru'] += node.capacity_total.hru
        totals['total_capacities']['mru'] += node.capacity_total.mru
        totals['total_capacities']['sru'] += node.capacity_total.sru

        totals['reserved_capacities']['cru'] += node.capacity_reserved.cru
        totals['reserved_capacities']['hru'] += node.capacity_reserved.hru
        totals['reserved_capacities']['mru'] += node.capacity_reserved.mru
        totals['reserved_capacities']['sru'] += node.capacity_reserved.sru

        totals['used_capacities']['cru'] += node.capacity_used.cru
        totals['used_capacities']['hru'] += node.capacity_used.hru
        totals['used_capacities']['mru'] += node.capacity_used.mru
        totals['used_capacities']['sru'] += node.capacity_used.sru
    
        if node.state == 'up':
            totals['nodes_up'] += 1
        else: 
            totals['nodes_down'] += 1
        
    return totals


@blueprint.route('/nodes', methods=['GET'])
def nodes_route():
    search_input = request.args.to_dict()
    nodes = client.farmer.node_find(**search_input).res
    farmers = client.farmer.farmers_get().res
    countries = {node.location.country for node in nodes}
    return render_template("dashboard/nodes.html", nodes=nodes,farmers=farmers,countries=countries)

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
        j.servers.gedis.latest.handler.handle_websocket(socket=socket, namespace="base")


@blueprint.route('/<page>.html')
def route_page(page):
    try:
        doc = ds.doc_get(page)
    except:
        doc = None
    return render_template('{name}/{page}.html'.format(name=name, page=page), name=name, doc=doc)