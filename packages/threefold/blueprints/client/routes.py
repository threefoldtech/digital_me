import json
from flask import redirect, session, render_template
from blueprints.client import blueprint
from .user import get_iyo_login_url, callback


@blueprint.route('/', methods=['GET'])
def login():
    if not session.get("iyo_authenticated"):
        return redirect(get_iyo_login_url())
    data = {
        "jwt": session['iyo_jwt'],
        "info": session['iyo_user_info']
    }
    return render_template("client/client.html", **data)


@blueprint.route('/callback', methods=['GET'])
def callback_route():
    return callback()
