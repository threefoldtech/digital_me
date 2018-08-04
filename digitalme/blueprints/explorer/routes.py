from flask import render_template, redirect, request
from blueprints.explorer import blueprint, name

TF_HOST = "localhost:23110"


@blueprint.route('/')
def route_default():
    return redirect('%s/index.html' % name)


@blueprint.route('/api/explorer/<path:path>')
def explorer_api(path):
    response = redirect('%s/%s' % (TF_HOST, path))
    response.headers.add("User-Agent", "Rivine-Agent")
    return response


@blueprint.route('/<page>.html')
def route_page(page):
    return render_template('{name}/{page}.html'.format(name=name, page=page))
