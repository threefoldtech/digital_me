# THIS FILE IS SAFE TO EDIT. It will not be overwritten when rerunning go-raml.

from flask import jsonify, request
from digitalme.blueprints.gridcapacity.models import FarmerRegistration, FarmerNotFoundError


def GetFarmerHandler(iyo_organization):
    try:
        farmer = FarmerRegistration.get(iyo_organization)
    except FarmerNotFoundError:
        return jsonify(), 404

    return farmer.ddict_hr, 200, {'Content-type': 'application/json'}
