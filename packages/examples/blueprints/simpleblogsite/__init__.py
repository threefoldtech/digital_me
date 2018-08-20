from flask import Blueprint
from jumpscale import j

name =  j.sal.fs.getDirName(__file__,True)
print("NAME::: ", name)
blueprint = Blueprint(
    '%s_blueprint'%name,
    __name__,
    url_prefix="/%s"%name,
    template_folder='templates',
    static_folder='static'
)
