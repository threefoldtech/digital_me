from flask import render_template, redirect, request, url_for
from blueprints.simpleblogsite import *
from jumpscale import j

login_manager = j.servers.web.latest.loader.login_manager

j.tools.markdowndocs.load("https://github.com/threefoldtech/jumpscale_weblibs/tree/master/docsites_examples/simpleblogsite")
ds = j.tools.markdowndocs.docsite_get("simpleblogsite")

from IPython import embed;embed(colors='Linux')

@blueprint.route('/')
def route_default():
    # return redirect(url_for('index_.html'))
    return redirect('/%s/index.html'%name)

@blueprint.route('/blog/<page>.html')
@blueprint.route('/blog/<page>')
def route_blog(page):
    
    
    return render_template('%s_%s.html'%(name, page),docsite=ds)


# # ds.doc_get(template)
# # @login_required
# @blueprint.route('/<template>.html')
# def route_template(template):
#     # from IPython import embed;embed(colors='Linux')
#     return render_template('%s_%s.html'%(name,template))

