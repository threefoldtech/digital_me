from requests.exceptions import HTTPError
from Jumpscale import j
from jose import jwt
from flask import redirect, session, render_template
from blueprints.client import blueprint
from .user import get_iyo_login_url, callback


@blueprint.route('/', methods=['GET'])
def login():
    if not session.get("iyo_authenticated"):
        return redirect(get_iyo_login_url())

    # Refresh jwt if expired
    if session.get("iyo_jwt"):
        claims = jwt.get_unverified_claims(session["iyo_jwt"])
        if j.clients.itsyouonline.jwt_is_expired(claims['exp']):
            try:
                session['iyo_jwt'] = j.clients.itsyouonline.refresh_jwt_token(jwt)
            except HTTPError:
                session.clear()
                return redirect(get_iyo_login_url())

    data = {
        "jwt": session['iyo_jwt'],
        "info": session['iyo_user_info']
    }
    return render_template("client/client.html", **data)


@blueprint.route('/callback', methods=['GET'])
def callback_route():
    return callback()
