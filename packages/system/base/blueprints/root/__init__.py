
from flask import Blueprint
from Jumpscale import j

name =  j.sal.fs.getDirName(__file__,True)
blueprint = Blueprint(
    '%s_blueprint'%name,
    __name__,
    url_prefix="/",
    template_folder='templates',
    static_folder='static'
)
