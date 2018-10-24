from flask import render_template, redirect, request, make_response
from blueprints.dashboard import *
from Jumpscale import j
from collections import Counter
import pycountry

# j.tools.threefold_farmer.load(reset=False)
client = j.servers.gedis.latest.client_get()
node_model = j.tools.threefold_farmer.bcdb.model_get('threefold.grid.node')
farmer_model = j.tools.threefold_farmer.bcdb.model_get('threefold.grid.farmer')


@blueprint.route('/node/<node_zos_id>')
def route_node(node_zos_id):
    node = client.farmer.node_find(node_zos_id=node_zos_id).res[0]
    heatmap_data = [{'latLng':[node.location.latitude, node.location.longitude],'name':node.location.country}]
    heatmap_data = j.data.serializers.json.dumps(heatmap_data)
    country_codes = [pycountry.countries.get(name=node.location.country).alpha_2]
    return render_template("dashboard/node.html", node=node,heatmap_data = heatmap_data, country_codes=country_codes)

@blueprint.route('/', methods=['GET'])
def route_default():
    search_input = request.args.to_dict()
    nodes = client.farmer.node_find(**search_input).res
    capacity_totals = calculate_capacities(nodes)
    heatmap_data = list({'latLng':[node.location.latitude, node.location.longitude],'name':node.location.country} for node in nodes if node.location.latitude
                           and node.location.longitude)
    heatmap_data = j.data.serializers.json.dumps(heatmap_data)
    country_codes = list(pycountry.countries.get(name=node.location.country).alpha_2 for node in nodes if node.location.latitude and node.location.longitude)
    return render_template("dashboard/index.html", nodes = nodes, heatmap_data = heatmap_data, country_codes = country_codes, totals = capacity_totals)

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
        
    totals['used_cap_perc_mru'] = (totals['used_capacities']['mru']/totals['total_capacities']['mru'])*100 if totals['total_capacities']['mru'] != 0 else 0
    totals['used_cap_perc_cru'] = (totals['used_capacities']['cru']/totals['total_capacities']['cru'])*100 if totals['total_capacities']['cru'] != 0 else 0
    totals['used_cap_perc_hru'] = (totals['used_capacities']['hru']/totals['total_capacities']['hru'])*100 if totals['total_capacities']['hru'] != 0 else 0
    totals['used_cap_perc_sru'] = (totals['used_capacities']['sru']/totals['total_capacities']['sru'])*100 if totals['total_capacities']['sru'] != 0 else 0

    totals['reserved_cap_perc_mru'] = (totals['reserved_capacities']['mru']/totals['total_capacities']['mru'])*100 if totals['total_capacities']['mru'] != 0 else 0
    totals['reserved_cap_perc_cru'] = (totals['reserved_capacities']['cru']/totals['total_capacities']['cru'])*100 if totals['total_capacities']['cru'] != 0 else 0
    totals['reserved_cap_perc_hru'] = (totals['reserved_capacities']['hru']/totals['total_capacities']['hru'])*100 if totals['total_capacities']['hru'] != 0 else 0
    totals['reserved_cap_perc_sru'] = (totals['reserved_capacities']['sru']/totals['total_capacities']['sru'])*100 if totals['total_capacities']['sru'] != 0 else 0

    return totals


@blueprint.route('/nodes', methods=['GET'])
def nodes_route():
    search_input = request.args.to_dict()
    nodes = client.farmer.node_find(**search_input).res

    farmers_list = farmer_model.get_all()
    farmers = {farmer.id:farmer for farmer in farmers_list}
    
    countries = {node.location.country for node in nodes}
    return render_template("dashboard/nodes.html", nodes = nodes,farmers = farmers,countries = countries)

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