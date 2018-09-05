# THIS FILE IS SAFE TO EDIT. It will not be overwritten when rerunning go-raml.
import os

from flask import request, redirect, url_for
from blueprints.gridcapacity.flask_itsyouonline import requires_auth

import json as JSON
import jsonschema
from jsonschema import Draft4Validator
from blueprints.gridcapacity.models import Farmer, Location
from .reverse_geocode import reverse_geocode

dir_path = os.path.dirname(os.path.realpath(__file__))
Farmer_schema = JSON.load(open(dir_path + '/schema/Farmer_schema.json'))
Farmer_schema_resolver = jsonschema.RefResolver('file://' + dir_path + '/schema/', Farmer_schema)
Farmer_schema_validator = Draft4Validator(Farmer_schema, resolver=Farmer_schema_resolver)

@requires_auth(org_from_request=True)
def RegisterFarmerHandler():
    wallet_addresses = []
    address = request.args.get('walletAddress')
    if address:
        wallet_addresses.append(address)

    farmer = Farmer.new()
    farmer.name = request.args['name']
    farmer.iyo_organization = request.args['organization']
    farmer.wallet_addresses = wallet_addresses
    farmAddress = request.args.get('farmAddress')
    if farmAddress:
        lat, lng = [float(x.strip()) for x in farmAddress.split(",")]
        continent, country, city = reverse_geocode(lat, lng)
        
        if continent and country and city:
            farmer.location.country = country
            farmer.location.continent = continent
            farmer.location.city = city
            farmer.location.longitude = lng
            farmer.location.latitude = lat
    Farmer.set(farmer)
    return redirect(url_for('gridcapacity_blueprint.farmer_registered'))
