#
# Itsyou.Online authentication helpers for Flask
#
import time
import uuid
from urllib.parse import urlencode
import requests
from flask import current_app, redirect, request, session
import flask_login
from jumpscale import j

__version__ = '0.0.1'

ITSYOUONLINEV1 = "https://itsyou.online/v1"

login_manager = j.servers.web.latest.loader.login_manager
login_manager.login_view = "/user/login"
dm_table = j.servers.gedis.latest.bcdb.table_get("dm_myself")


class User(flask_login.UserMixin):
    def __init__(self, uid, name, emails):
        self.id = uid
        self.name = name
        self.email = emails


@login_manager.user_loader
def user_loader(uid):
    if not dm_table.db.exists(int(uid)):
        return
    user_data = dm_table.get(int(uid))
    user = User(user_data.id, user_data.name, user_data.email)
    return user


def login_with_iyo_user(user_info):
    user_ids = dm_table.db.list()
    for user_id in user_ids:
        user = dm_table.get(user_id)
        if user.iyouser == user_info['username']:
            break
    else:
        user = dm_table.set(data={
            "name": "{} {}".format(user_info['firstname'], user_info['lastname']),
            "iyouser": user_info['username'],
            "email": [email['emailaddress'] for email in user_info['emailaddresses']]
        })
    logged_user = User(user.id, user.name, user.email)
    flask_login.login_user(logged_user)
    return


def callback():
    code = request.args.get("code")
    state = request.args.get("state")
    session_state = session.get("_iyo_state")
    on_complete_uri = session.get("_iyo_auth_complete_uri")
    if not on_complete_uri:
        return "Invalid request.", 400
    if session_state != state:
        return "Invalid state received. Cannot authenticate request!", 400
    if not code:
        return "Invalid code received. Cannot authenticate request!", 400
    # Get access token
    config = current_app.config["IYO_CONFIG"]
    organization = config["organization"]
    auth_org = session['_iyo_organization']
    params = {
        "code": code,
        "state": state,
        "grant_type": "authorization_code",
        "client_id": organization,
        "client_secret": config["client_secret"],
        "redirect_uri": config["callback_uri"],
    }
    base_url = "{}/oauth/access_token?".format(ITSYOUONLINEV1)
    url = base_url + urlencode(params)
    response = requests.post(url)
    response.raise_for_status()
    response = response.json()
    scope_parts = response["scope"].split(",")
    if not "user:memberof:{}".format(auth_org) in scope_parts:
        return "User is not authorized.", 403
    access_token = response["access_token"]
    username = response["info"]["username"]
    # Get user info
    session['iyo_user_info'] = _get_info(username, access_token=access_token)
    # Register the user into bcdb:
    login_with_iyo_user(session['iyo_user_info'])
    session['_iyo_authenticated'] = time.time()
    if config['get_jwt']:
        # Create JWT
        scope = "user:memberof:{}".format(auth_org)
        if config['offline_access']:
            scope += ",offline_access"
        params = dict(scope=scope)
        jwt_url = "https://itsyou.online/v1/oauth/jwt?%s" % urlencode(params)
        headers = {"Authorization": "token %s" % access_token}
        response = requests.get(jwt_url, headers=headers)
        response.raise_for_status()
        session['iyo_jwt'] = response.text
    return redirect(on_complete_uri)


def _get_info(username, access_token=None, jwt=None):
    if access_token:
        headers = {"Authorization": "token %s" % access_token}
    else:
        headers = {"Authorization": "Bearer %s" % jwt}
    user_info_url = "https://itsyou.online/api/users/%s/info" % username
    response = requests.get(user_info_url, headers=headers)
    response.raise_for_status()
    return response.json()


def get_iyo_login_url():
    config = current_app.config["IYO_CONFIG"]
    organization = config['organization']
    scopes = ["user:memberof:{}".format(organization)]
    if config["scope"]:
        scopes.append(",".join(config['scope']))
    scope = ','.join(scopes)
    state = str(uuid.uuid4())
    session["_iyo_state"] = state
    session['_iyo_organization'] = organization
    session["_iyo_auth_complete_uri"] = request.args.get("next") or "/"
    params = {
        "response_type": "code",
        "client_id": config["organization"],
        "redirect_uri": config["callback_uri"],
        "scope": scope,
        "state": state
    }
    base_url = "{}/oauth/authorize?".format(ITSYOUONLINEV1)
    login_url = base_url + urlencode(params)
    return login_url
