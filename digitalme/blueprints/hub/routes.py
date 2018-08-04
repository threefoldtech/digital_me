import os
import shutil
import json
from stat import *
from blueprints.hub import *
from flask import request, render_template, abort, make_response, send_from_directory
from werkzeug.utils import secure_filename
# from werkzeug.contrib.fixers import ProxyFix
from .config import config
from blueprints.hub.hub.flist import HubPublicFlist
# from hub.itsyouonline import ItsYouChecker
from blueprints.hub.hub.docker import HubDocker
from blueprints.hub.hub.merge import HubMerger

#
# runtime configuration
# theses location should works out-of-box if you use default settings
#
base_path = os.path.dirname(os.path.realpath(__file__))

config['public-directory'] = os.path.join(base_path, "public/users/")
config['flist-work-directory'] = os.path.join(base_path, "workdir/temp")
config['docker-work-directory'] = os.path.join(base_path, "workdir/temp")
config['upload-directory'] = os.path.join(base_path, "workdir/distfiles")
config['allowed-extensions'] = {'.tar.gz'}

print("[+] upload directory: %s" % config['upload-directory'])
print("[+] flist creation  : %s" % config['flist-work-directory'])
print("[+] public directory: %s" % config['public-directory'])


#
# initialize flask application
#
# app = Flask(__name__)
# app.wsgi_app = ItsYouChecker(app.wsgi_app)
# app.wsgi_app = ProxyFix(app.wsgi_app)
# app.url_map.strict_slashes = False

######################################
#
# TEMPLATES MANIPULATION
#
######################################


def allowed_file(filename, validate=False):
    if validate:
        return filename.endswith(".flist")

    for ext in config['allowed-extensions']:
        if filename.endswith(ext):
            return True

    return False


def global_template(filename, args):
    args['debug'] = config['DEBUG']
    return render_template(filename, **args)


def file_from_flist(filename):
    clean_file_name = filename
    for ext in config['allowed-extensions']:
        if clean_file_name.endswith(ext):
            clean_file_name = clean_file_name[:-len(ext)]

    return clean_file_name


def upload_success(flist_name, files_count, username=None):
    if username is None:
        username = request.environ['username']

    settings = {
        'username': username,
        'accounts': request.environ['accounts'],
        'flistname': flist_name,
        'filescount': files_count,
        'flisturl': "%s/%s/%s" % (config['PUBLIC_WEBADD'], username, flist_name),
        'ardbhost': 'ardb://%s:%d' % (config['PUBLIC_ARDB_HOST'], config['PUBLIC_ARDB_PORT']),
    }

    return global_template("success.html", settings)


def internal_redirect(target, error=None):
    settings = {
        'username': request.environ['username'],
        'accounts': request.environ['accounts'],
    }

    if error:
        settings['error'] = error

    return global_template(target, settings)


def flist_merge_post():
    sources = request.form.getlist('flists[]')
    target = request.form['name']

    return flist_merge_data(sources, target)


def flist_merge_data(sources, target):
    data = {'error': None, 'sources': sources, 'target': target}

    if not isinstance(sources, list):
        data['error'] = 'malformed json request'
        return data

    if len(data['sources']) == 0:
        data['error'] = "no source found"
        return data

    if not data['target']:
        data['error'] = "missing build (target) name"
        return data

    if "/" in data['target']:
        data['error'] = "build name not allowed"
        return data

    if not data['target'].endswith('.flist'):
        data['target'] += '.flist'

    return data


######################################
#
# ROUTING ACTIONS
#
######################################


@blueprint.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if not request.environ['username']:
        return "Access denied."

    username = request.environ['username']

    if request.method == 'POST':
        response = api_flist_upload(request, username)

        if response['status'] == 'success':
            return upload_success(response['flist'], response['count'])

        if response['status'] == 'error':
            return internal_redirect("upload.html", response['message'])

    return internal_redirect("upload.html")


@blueprint.route('/upload-flist', methods=['GET', 'POST'])
def upload_file_flist():
    if not request.environ['username']:
        return "Access denied."

    username = request.environ['username']

    if request.method == 'POST':
        response = api_flist_upload(request, username, validate=True)

        if response['status'] == 'success':
            return upload_success(response['flist'], response['count'])

        if response['status'] == 'error':
            return internal_redirect("upload-flist.html", response['message'])

    return internal_redirect("upload-flist.html")


@blueprint.route('/merge', methods=['GET', 'POST'])
@login_required
def flist_merge():
    if not request.environ['username']:
        return "Access denied."

    username = request.environ['username']

    if request.method == 'POST':
        data = flist_merge_post()
        print(data)

        if data['error']:
            return internal_redirect("merge.html", data['error'])

        merger = HubMerger(config, username, data['target'])
        status = merger.merge(data['sources'])

        if not status:
            variables = {'error': status}
            return global_template("merge.html", variables)

        return upload_success(data['target'], 0)

    # Merge page
    return internal_redirect("merge.html")


@blueprint.route('/docker-convert', methods=['GET', 'POST'])
def docker_handler():
    if not request.environ['username']:
        return "Access denied."

    username = request.environ['username']

    if request.method == 'POST':
        if not request.form.get("docker-input"):
            return internal_redirect("docker.html", "missing docker image name")

        docker = HubDocker(config)
        response = docker.convert(request.form.get("docker-input"), username)

        if response['status'] == 'success':
            return upload_success(response['flist'], response['count'])

        if response['status'] == 'error':
            return internal_redirect("docker.html", response['message'])

    # Docker page
    return internal_redirect("docker.html")


######################################
#
# ROUTING NAVIGATION
#
######################################
@blueprint.route('/')
def show_users():
    return global_template("users.html", {})


@blueprint.route('/<username>')
def show_user(username):
    flist = HubPublicFlist(config, username, "unknown")
    if not flist.user_exists:
        abort(404)

    return global_template("user.html", {'targetuser': username})


@blueprint.route('/<username>/<flist>.md')
def show_flist_md(username, flist):
    flist = HubPublicFlist(config, username, flist)
    if not flist.file_exists:
        abort(404)

    variables = {
        'targetuser': username,
        'flistname': flist.filename,
        'flisturl': "%s/%s/%s" % (config['PUBLIC_WEBADD'], username, flist.filename),
        'ardbhost': 'ardb://%s:%d' % (config['PUBLIC_ARDB_HOST'], config['PUBLIC_ARDB_PORT']),
        'checksum': flist.checksum
    }

    return global_template("preview.html", variables)


@blueprint.route('/<username>/<flist>.txt')
def show_flist_txt(username, flist):
    flist = HubPublicFlist(config, username, flist)
    if not flist.file_exists:
        abort(404)

    text = "File:     %s\n" % flist.filename
    text += "Uploader: %s\n" % username
    text += "Source:   %s/%s/%s\n" % (config['PUBLIC_WEBADD'], username, flist.filename)
    text += "Storage:  ardb://%s:%d\n" % (config['PUBLIC_ARDB_HOST'], config['PUBLIC_ARDB_PORT'])
    text += "Checksum: %s\n" % flist.checksum

    response = make_response(text)
    response.headers["Content-Type"] = "text/plain"

    return response


@blueprint.route('/<username>/<flist>.json')
def show_flist_json(username, flist):
    flist = HubPublicFlist(config, username, flist)
    if not flist.file_exists:
        abort(404)

    data = {
        'flist': flist,
        'uploader': username,
        'source': "%s/%s/%s" % (config['PUBLIC_WEBADD'], username, flist),
        'storage': "ardb://%s:%d" % (config['PUBLIC_ARDB_HOST'], config['PUBLIC_ARDB_PORT']),
        'checksum': flist.checksum
    }

    response = make_response(json.dumps(data) + "\n")
    response.headers["Content-Type"] = "application/json"

    return response


@blueprint.route('/<username>/<flist>.flist')
def download_flist(username, flist):
    flist = HubPublicFlist(config, username, flist)
    return send_from_directory(directory=flist.user_path, filename=flist.filename)


@blueprint.route('/<username>/<flist>.flist.md5')
def checksum_flist(username, flist):
    flist = HubPublicFlist(config, username, flist)
    flist_hash = flist.checksum

    if not flist_hash:
        abort(404)

    response = make_response(flist_hash + "\n")
    response.headers["Content-Type"] = "text/plain"

    return response


######################################
#
# ROUTING API
#
######################################
@blueprint.route('/api/flist')
def api_list():
    repositories = api_repositories()
    output = []

    for user in repositories:
        target = os.path.join(config['public-directory'], user['name'])

        # ignore files (eg: .keep file)
        if not os.path.isdir(target):
            continue

        flists = sorted(os.listdir(target))
        for flist in flists:
            output.append("%s/%s" % (user['name'], flist))

    response = make_response(json.dumps(output) + "\n")
    response.headers["Content-Type"] = "application/json"

    return response


@blueprint.route('/api/repositories')
def api_list_repositories():
    repositories = api_repositories()

    response = make_response(json.dumps(repositories) + "\n")
    response.headers["Content-Type"] = "application/json"

    return response


@blueprint.route('/api/flist/<username>')
def api_user_contents(username):
    flist = HubPublicFlist(config, username, "unknown")
    if not flist.user_exists:
        abort(404)

    files = sorted(os.listdir(flist.user_path))
    contents = []

    for file in files:
        filepath = os.path.join(config['public-directory'], username, file)
        stat = os.lstat(filepath)

        if S_ISLNK(stat.st_mode):
            target = os.readlink(filepath)

            contents.append({
                'name': file,
                'size': "--",
                'updated': int(stat.st_mtime),
                'type': 'symlink',
                'target': target,
            })

        else:
            contents.append({
                'name': file,
                'size': "%.2f KB" % (stat.st_size / 1024),
                'updated': int(stat.st_mtime),
                'type': 'regular',
            })

    response = make_response(json.dumps(contents) + "\n")
    response.headers["Content-Type"] = "application/json"

    return response


@blueprint.route('/api/flist/<username>/<flist>', methods=['GET', 'INFO'])
def api_inspect(username, flist):
    flist = HubPublicFlist(config, username, flist)

    if not flist.user_exists:
        return api_response("user not found", 404)

    if not flist.file_exists:
        return api_response("source not found", 404)

    contents = ""
    if request.method == 'GET':
        contents = api_contents(flist)

    if request.method == 'INFO':
        contents = api_flist_info(flist)

    response = make_response(json.dumps(contents) + "\n")
    response.headers["Content-Type"] = "application/json"

    return response


@blueprint.route('/api/flist/me', methods=['GET'])
def api_my_myself():
    if not request.environ['username']:
        return api_response("Access denied", 401)

    return api_response(extra={"username": request.environ['username']})


@blueprint.route('/api/flist/me/<flist>', methods=['GET', 'DELETE'])
def api_my_inspect(flist):
    if not request.environ['username']:
        return api_response("Access denied", 401)

    username = request.environ['username']

    if request.method == 'DELETE':
        return api_delete(username, flist)

    return api_inspect(username, flist)


@blueprint.route('/api/flist/me/<source>/link/<linkname>', methods=['GET'])
def api_my_flist(source, linkname):
    if not request.environ['username']:
        return api_response("Access denied", 401)

    username = request.environ['username']

    return api_symlink(username, source, linkname)


@blueprint.route('/api/flist/me/<source>/rename/<destination>')
def api_my_rename(source, destination):
    if not request.environ['username']:
        return api_response("Access denied", 401)

    username = request.environ['username']
    flist = HubPublicFlist(config, username, source)
    destflist = HubPublicFlist(config, username, destination)

    if not flist.user_exists:
        return api_response("user not found", 404)

    if not flist.file_exists:
        return api_response("source not found", 404)

    os.rename(flist.target, destflist.target)

    return api_response()


@blueprint.route('/api/flist/me/promote/<sourcerepo>/<sourcefile>/<localname>', methods=['GET'])
def api_my_promote(sourcerepo, sourcefile, localname):
    if not request.environ['username']:
        return api_response("Access denied", 401)

    username = request.environ['username']

    return api_promote(username, sourcerepo, sourcefile, localname)


@blueprint.route('/api/flist/me/upload', methods=['POST'])
def api_my_upload():
    if not request.environ['username']:
        return api_response("Access denied", 401)

    username = request.environ['username']

    response = api_flist_upload(request, username)
    if response['status'] == 'success':
        if config['DEBUG']:
            return api_response(extra={'name': response['flist'], 'files': response['count'], 'timing': {}})

        else:
            return api_response(extra={'name': response['flist'], 'files': response['count']})

    if response['status'] == 'error':
        return api_response(response['message'], 500)


@blueprint.route('/api/flist/me/upload-flist', methods=['POST'])
def api_my_upload_flist():
    if not request.environ['username']:
        return api_response("Access denied", 401)

    username = request.environ['username']

    response = api_flist_upload(request, username, validate=True)
    if response['status'] == 'success':
        if config['DEBUG']:
            return api_response(extra={'name': response['flist'], 'files': response['count'], 'timing': {}})

        else:
            return api_response(extra={'name': response['flist'], 'files': response['count']})

    if response['status'] == 'error':
        return api_response(response['message'], 500)


@blueprint.route('/api/flist/me/merge/<target>', methods=['POST'])
def api_my_merge(target):
    if not request.environ['username']:
        return api_response("Access denied", 401)

    username = request.environ['username']

    sources = request.get_json(silent=True, force=True)
    data = flist_merge_data(sources, target)

    if data['error']:
        return api_response(data['error'], 500)

    merger = HubMerger(config, username, data['target'])
    status = merger.merge(data['sources'])

    if not status:
        return api_response(status, 500)

    return api_response()


@blueprint.route('/api/flist/me/docker', methods=['POST'])
def api_my_docker():
    if not request.environ['username']:
        return api_response("Access denied", 401)

    username = request.environ['username']

    if not request.form.get("image"):
        return api_response("missing docker image name", 400)

    docker = HubDocker(config)
    response = docker.convert(request.form.get("image"), username)

    if response['status'] == 'success':
        return api_response(extra={'name': response['flist']})

    if response['status'] == 'error':
        return api_response(response['message'], 500)

    return api_response("unexpected docker convert error", 500)


######################################
#
# API IMPLEMENTATION
#
######################################
def api_delete(username, source):
    flist = HubPublicFlist(config, username, source)

    if not flist.user_exists:
        return api_response("user not found", 404)

    if not flist.file_exists:
        return api_response("source not found", 404)

    os.unlink(flist.target)

    return api_response()


def api_symlink(username, source, linkname):
    flist = HubPublicFlist(config, username, source)
    linkflist = HubPublicFlist(config, username, linkname)

    if not flist.user_exists:
        return api_response("user not found", 404)

    if not flist.file_exists:
        return api_response("source not found", 404)

    # remove previous symlink if existing
    if os.path.islink(linkflist.target):
        os.unlink(linkflist.target)

    # if it was not a link but a regular file, we don't overwrite
    # existing flist, we only allows updating links
    if os.path.isfile(linkflist.target):
        return api_response("link destination is already a file", 401)

    cwd = os.getcwd()
    os.chdir(flist.user_path)

    os.symlink(flist.filename, linkflist.filename)
    os.chdir(cwd)

    return api_response()


def api_promote(username, sourcerepo, sourcefile, targetname):
    flist = HubPublicFlist(config, sourcerepo, sourcefile)
    destination = HubPublicFlist(config, username, targetname)

    if not flist.user_exists:
        return api_response("user not found", 404)

    if not flist.file_exists:
        return api_response("source not found", 404)

    # remove previous file if existing
    if os.path.exists(destination.target):
        os.unlink(destination.target)

    print("[+] promote: %s -> %s" % (flist.target, destination.target))
    shutil.copy(flist.target, destination.target)

    return api_response()


def api_flist_upload(req, username, validate=False):
    # check if the post request has the file part
    if 'file' not in req.files:
        return {'status': 'error', 'message': 'no file found'}

    file = req.files['file']

    # if user does not select file, browser also
    # submit a empty part without filename
    if file.filename == '':
        return {'status': 'error', 'message': 'no file selected'}

    if not allowed_file(file.filename, validate):
        return {'status': 'error', 'message': 'this file is not allowed'}

    #
    # processing the file
    #
    filename = secure_filename(file.filename)

    print("[+] saving file")
    source = os.path.join(config['upload-directory'], filename)
    file.save(source)

    cleanfilename = file_from_flist(filename)
    flist = HubPublicFlist(config, username, cleanfilename)

    # validate if the flist exists
    if not validate:
        # extracting archive to workspace
        workspace = flist.raw.workspace()

        # create the flist
        flist.raw.unpack(source, workspace.name)
        flist.raw.initialize(workspace.name)
        flist.raw.insert(workspace.name)
        flist.raw.upload()

    else:
        # loads content
        flist.raw.loads(source)
        if not flist.raw.validate():
            return {'status': 'error', 'message': 'unauthorized upload, contents is not fully present on backend'}

    flist.raw.commit()
    flist.user_create()
    flist.raw.pack(flist.target)

    # removing uploaded source file
    os.unlink(source)

    return {'status': 'success', 'flist': flist.filename, 'home': username, 'count': 0, 'timing': {}}


def api_repositories():
    root = sorted(os.listdir(config['public-directory']))
    output = []

    for user in root:
        target = os.path.join(config['public-directory'], user)

        # ignore files (eg: .keep file)
        if not os.path.isdir(target):
            continue

        official = (user in config['PUBLIC_OFFICIALS'])
        output.append({'name': user, 'official': official})

    return output


def api_contents(flist):
    flist.raw.loads(flist.target)
    contents = flist.raw.listing()

    return contents


def api_flist_info(flist):
    stat = os.lstat(flist.target)
    file = os.path.basename(flist.target)

    contents = {
        'name': file,
        'size': stat.st_size,
        'updated': int(stat.st_mtime),
        'type': 'regular',
        'md5': flist.checksum,
    }

    if S_ISLNK(stat.st_mode):
        contents['type'] = 'symlink'
        contents['target'] = flist.target
        contents['size'] = 0

    return contents


def api_response(error=None, code=200, extra=None):
    reply = {"status": "success"}

    if error:
        reply = {"status": "error", "message": error}

    if extra:
        reply['payload'] = extra

    response = make_response(json.dumps(reply) + "\n", code)
    response.headers["Content-Type"] = "application/json"
    return response
