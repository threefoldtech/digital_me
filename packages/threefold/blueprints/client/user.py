import time
import uuid
import os
from Jumpscale import j
from urllib.parse import urlencode
import requests
from flask import request, session, redirect

ITSYOUONLINEV1 = "https://itsyou.online/v1"
dir_path = os.path.dirname(os.path.realpath(__file__))
iyo_config_path = os.path.join(dir_path, "iyo.json")
config = j.data.serializers.json.load(iyo_config_path)


def callback():
    code = request.args.get("code")
    state = request.args.get("state")
    session_state = session.get("_iyo_state")
    if session_state != state:
        return "Invalid state received. Cannot authenticate request!", 400
    if not code:
        return "Invalid code received. Cannot authenticate request!", 400
    # Get access token
    organization = config["organization"]
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
    access_token = response["access_token"]
    username = response["info"]["username"]
    # Get user info
    session['iyo_user_info'] = _get_info(username, access_token=access_token)
    session['iyo_authenticated'] = time.time()
    # Create JWT
    if "offline_access" not in config['scope']:
        config['scope'].append("offline_access")
    scope = ",".join(config['scope'])
    params = dict(scope=scope, store_info="true")
    jwt_url = "https://itsyou.online/v1/oauth/jwt?%s" % urlencode(params)
    headers = {"Authorization": "token %s" % access_token}
    response = requests.get(jwt_url, headers=headers)
    response.raise_for_status()
    session['iyo_jwt'] = response.text
    return redirect("/client")


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
    scope = ",".join(config['scope'])
    state = str(uuid.uuid4())
    session["_iyo_state"] = state
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
