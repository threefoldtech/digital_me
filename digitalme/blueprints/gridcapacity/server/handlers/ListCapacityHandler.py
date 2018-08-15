# THIS FILE IS SAFE TO EDIT. It will not be overwritten when rerunning go-raml.

from digitalme.blueprints.gridcapacity.models import NodeRegistration
from flask import request, jsonify
from io import StringIO


def ListCapacityHandler():
    nodes = []
    country = request.values.get('country')
    mru = request.values.get('mru')
    cru = request.values.get('cru')
    hru = request.values.get('hru')
    sru = request.values.get('sru')
    farmer = request.values.get('farmer')
    nodes = NodeRegistration.search(country, mru, cru, hru, sru, farmer)
    output = []
    for node in nodes:
        if node.farmer.location and node.farmer.location.latitude and node.farmer.location.longitude:
            node.location = node.farmer.location
        d = node.ddict_hr
        d['node_id'] = d.pop('id')
        d['farmer_id'] = d.pop('farmer')
        output.append(d)

    return jsonify(output)
