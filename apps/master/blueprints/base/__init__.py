# from flask import Blueprint
# from jumpscale import j

# staticpath = j.clients.git.getContentPathFromURLorPath("https://github.com/threefoldtech/jumpscale_/web_libs/tree/master/static")

# blueprint = Blueprint(
#     'base_blueprint',
#     __name__,
#     url_prefix='',
#     template_folder='templates',
#     static_folder=staticpath
# )

# blueprint = Blueprint(
#     'base_blueprint',
#     __name__,
#     url_prefix='/base',
#     template_folder='templates',
#     static_folder='static'
# )


from flask import Blueprint
from jumpscale import j

name =  j.sal.fs.getDirName(__file__,True)
staticpath = j.clients.git.getContentPathFromURLorPath("https://github.com/threefoldtech/jumpscale_/web_libs/tree/master/static")

#create link to static dir on jumpscale web libs
localstat_path = "%s/static"%j.sal.fs.getDirName(__file__)
j.sal.fs.remove(localstat_path)
j.sal.fs.symlink(staticpath,localstat_path, overwriteTarget=True)

blueprint = Blueprint(
    '%s_blueprint'%name,
    __name__,
    url_prefix="/%s"%name,
    template_folder='templates',
    static_folder='static'
)
