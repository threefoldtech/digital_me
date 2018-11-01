from flask import render_template
from blueprints.home import blueprint


@blueprint.route('/', methods=['GET'])
def route_index():
    return render_template('home/index.html')
