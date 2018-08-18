# THIS FILE IS SAFE TO EDIT. It will not be overwritten when rerunning go-raml.
from flask import request, jsonify
from digitalme.blueprints.gridcapacity.models import FarmerRegistration

def ListFarmersHandler():
    farmers = FarmerRegistration.list()
    output = []
    for farmer in farmers:
        f = farmer.ddict_hr
        f['iyo_organization'] = f.pop('id')
        output.append(f)
    return jsonify(output)
