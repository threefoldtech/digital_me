from flask import render_template, redirect, request, url_for
from jumpscale import j
from blueprints.gridcapacity import blueprint
login_manager = j.servers.web.latest.loader.login_manager
from digitalme.blueprints.gridcapacity.server import handlers
import os
from flask import send_from_directory, render_template, request, session, abort, redirect
from .flask_itsyouonline import requires_auth, force_invalidate_session, ITSYOUONLINE_KEY, callback
from .models import NodeRegistration, FarmerRegistration, FarmerNotFoundError
import jwt

dir_path = os.path.dirname(os.path.realpath(__file__))

@blueprint.route('/api/farmer_create', methods=['GET'])
def RegisterFarmer():
    """
    Register a farmer
    It is handler for GET /api/farmer_create
    """
    return handlers.RegisterFarmerHandler()


@blueprint.route('/api/farmer_update', methods=['GET'])
def UpdateFarmer():
    """
    Update a farmer
    It is handler for GET /api/farmer_update
    """
    return handlers.UpdateFarmerHandler()


@blueprint.route('/api/farmers', methods=['GET'])
def ListFarmers():
    """
    List Farmers
    It is handler for GET /api/farmers
    """
    return handlers.ListFarmersHandler()


@blueprint.route('/api/farmers/<iyo_organization>', methods=['GET'])
def GetFarmer(iyo_organization):
    """
    Get detail about a farmer
    It is handler for GET /api/farmers/<iyo_organization>
    """
    return handlers.GetFarmerHandler(iyo_organization)


@blueprint.route('/api/nodes', methods=['GET'])
def ListCapacity():
    """
    List all the nodes capacity
    It is handler for GET /api/nodes
    """
    return handlers.ListCapacityHandler()


@blueprint.route('/api/nodes', methods=['POST'])
def RegisterCapacity():
    """
    Register a node capacity
    It is handler for POST /api/nodes
    """
    return handlers.RegisterCapacityHandler()


@blueprint.route('/api/nodes/<node_id>', methods=['GET'])
def GetCapacity(node_id):
    """
    Get detail about capacity of a node
    It is handler for GET /api/nodes/<node_id>
    """
    return handlers.GetCapacityHandler(node_id)


@blueprint.route('/api/nodes/<node_id>/reserved', methods=['PUT'])
def UpdateReservedCapacity(node_id):
    """
    Mark some capacity on a node to be reserved
    It is handler for PUT /api/nodes/<node_id>/reserved
    """
    return handlers.UpdateReservedCapacityHandler(node_id)


@blueprint.route('/api/nodes/<node_id>/actual', methods=['PUT'])
def UpdateActualUsedCapacity(node_id):
    """
    Set the actual usage of the capacity of a node
    It is handler for PUT /api/nodes/<node_id>/actual
    """
    return handlers.UpdateActualUsedCapacityHandler(node_id)

@blueprint.route('/static/<path:path>')
def send_js(path):
    return send_from_directory(dir_path, os.path.join('static', path))


@blueprint.route('/', methods=['GET'])
def capacity():
    countries = NodeRegistration.all_countries()
    farmers = FarmerRegistration.list(order='name')

    nodes = []
    form = {
        'mru': 0,
        'cru': 0,
        'sru': 0,
        'hru': 0,
        'country': '',
    }

    if len(request.args) != 0:
        for unit in ['mru', 'cru', 'sru', 'hru']:
            u = request.args.get(unit) or None
            if u:
                form[unit] = int(u)

        form['country'] = request.args.get('country') or ''
        form['farmer'] = request.args.get('farmer') or ''

        form['page'] = int(request.args.get('page') or 1)
        form['per_page'] = int(request.args.get('pre_page') or 20)

        nodes = NodeRegistration.search(**form, order='-updated')

    return render_template('capacity.html', nodes=nodes, form=form, countries=countries, farmers=farmers)


@blueprint.route('/farmers', methods=['GET'])
def list_farmers():
    farmers = FarmerRegistration.list(order='name')
    return render_template('farmers.html', farmers=farmers)


@blueprint.route('/farm_registered', methods=['GET'])
def farmer_registered():
    jwt = session['iyo_jwt']
    return render_template('farm_registered.html', jwt=jwt)


@blueprint.route('/farm_updated', methods=['GET'])
def farmer_updated():
    jwt = session['iyo_jwt']
    return render_template('farm_updated.html', jwt=jwt)


@blueprint.route('/api', methods=['GET'])
def api_index():
    return render_template('api.html')


@blueprint.route('/register_farm', methods=['GET'])
def register_farmer():
    return render_template('register_farm.html')


@blueprint.route('/edit_farm/<organization>', methods=['GET'])
def edit_farmer(organization):
    @requires_auth(org_from_request=organization)
    def handler():
        jwt_string = session['iyo_jwt']
        jwt_info = jwt.decode(jwt_string, ITSYOUONLINE_KEY)
        scopes = jwt_info['scope']
        for scope in scopes:
            if organization in scope:
                break
        else:
            # invalidate iyo_authenticated to retry login with the new scope.
            force_invalidate_session()

            return redirect("/edit_farm/{}".format(organization))
        try:
            farmer = FarmerRegistration.get(organization)
        except FarmerNotFoundError as e:
            abort(404)
        else:
            return render_template('edit_farm.html', farmer=farmer)
    return handler()


# IYO
@blueprint.route('/callback', methods=['GET'])
def iyo_callback():
    def handler():
        return callback()
    return handler()