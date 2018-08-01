import io
from flask import render_template, redirect, send_file
from blueprints.simpleblogsite import *
from jumpscale import j

login_manager = j.servers.web.latest.loader.login_manager

j.tools.markdowndocs.load(
    "https://github.com/threefoldtech/jumpscale_weblibs/tree/master/docsites_examples/simpleblogsite",
    name="simpleblogsite")
ds = j.tools.markdowndocs.docsite_get("simpleblogsite")


def image_path_get(image):
    file_path = ds.file_get(image)
    return file_path


@blueprint.route('/')
@blueprint.route('/index')
def route_default():
    return redirect('/%s/index.html' % name)


# e.g. http://localhost:5050/simpleblogsite/blog/10x-times-power
@blueprint.route('/blog/<blogname>.html')
@blueprint.route('/blog/<blogname>')
def route_blog(blogname):
    doc = ds.doc_get(blogname)
    return render_template('%s_blog.html' % (name), ds=ds, name=name,
                           blogname=blogname, doc=doc)


# @login_required
@blueprint.route('/<template>.html')
def route_template(template):
    # from IPython import embed;embed(colors='Linux')
    doc = ds.doc_get(template)
    return render_template('%s_%s.html' % (name, template), ds=ds, doc=doc)


@blueprint.route('/image/<image>')
def route_image(image):
    file_path = image_path_get(image)
    with open(file_path, 'rb') as bites:
        return send_file(
            io.BytesIO(bites.read()),
            attachment_filename=image
        )
