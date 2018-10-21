from flask import render_template, redirect, request, url_for
from Jumpscale import j
from blueprints.base import blueprint

login_manager = j.servers.web.latest.loader.login_manager


@blueprint.route('/')
def route_root():
    j.shell()
    return redirect(url_for('base_blueprint.login'))


