from flask import Blueprint, request
from jumpscale import j

name = j.sal.fs.getDirName(__file__, True)

blueprint = Blueprint(
    '%s_blueprint' % name,
    __name__,
    url_prefix="/%s" % name,
    template_folder='templates',
    static_folder='static'
)


# DUMMY method till we implement login in digital me
def login_required(r):
    request.environ['username'] = "ahamdy"
    request.environ['accounts'] = ['ahamdy']
    return


blueprint.context_processor(login_required)
