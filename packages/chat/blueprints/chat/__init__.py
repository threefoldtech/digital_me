from flask import Blueprint
from Jumpscale import j

name = j.sal.fs.getDirName(__file__, True)

blueprint = Blueprint(
    '%s_blueprint'%name,
    __name__,
    url_prefix="/%s"%name,
    template_folder='templates',
    static_folder='static'
)

ws_blueprint = Blueprint('%s_wsblueprint' % name, __name__, url_prefix="/%s"%name)
