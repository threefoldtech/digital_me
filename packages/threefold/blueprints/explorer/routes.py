from flask import render_template, redirect, request
from blueprints.explorer import blueprint, name
from Jumpscale import j

TF_HOST = "localhost:23110"

schedule = j.servers.gedis.latest.job_schedule

@blueprint.route('/')
def route_default():
    return redirect('%s/index.html' % name)

@blueprint.route('/test/')
def route_page():

    def test(x):
        import time
        print("!!!!")
        time.sleep(10)
        return(x)

    res = schedule(test, timeout=600, wait=True, depends_on=None, x=1)

    return res


@blueprint.route('/api/explorer/<path:path>')
def explorer_api(path):
    response = redirect('%s/%s' % (TF_HOST, path))
    response.headers.add("User-Agent", "Rivine-Agent")
    return response


@blueprint.route('/<page>.html')
def route_page(page):
    return render_template('{name}/{page}.html'.format(name=name, page=page))

