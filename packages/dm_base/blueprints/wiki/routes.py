from blueprints.wiki import blueprint
from flask import render_template, send_file, request
from flask import abort, redirect, url_for

import io

# from flask_login import login_required

from werkzeug.routing import BaseConverter
from Jumpscale import j


@blueprint.route('/index')
@blueprint.route('/')
def index():
    return redirect("wiki/foundation")


@blueprint.route('')
def index_sub(sub):
    return render_template('index_docsify.html')


@blueprint.route('/<path:subpath>')
def wiki_route(subpath, methods=['GET', 'POST']):
    base_url = request.url.split('wiki')[0] + 'wiki'
    subpath=subpath.strip("/")


    parts = subpath.split("/")

    if len(parts)==1: #"readme" in parts[0].lower() or "index" in parts[0].lower()
        #means we are in root of a wiki, need to load the html 
        return render_template('index_docsify.html')

    if len(parts)<2:
        return render_template('error_notfound.html',url=subpath)
        
    wikicat = parts[0].lower().strip()

    parts = parts[1:]

    url = "/".join(parts)

    ds = j.tools.docsites.docsite_get(wikicat, die=False)
    if ds == None:
        return "Cannot find docsite with name:%s" % wikicat

    if len(parts)>0 and parts[0].startswith("verify"):
        return ds.verify()

    if len(parts)>0 and parts[0].startswith("errors"):
        return ds.errors


    #if binary file, return
    name = parts[-1]
    if not name.endswith(".md"):
        file_path = ds.file_get(name)
        with open(file_path, 'rb') as bites:
            return send_file(
                        io.BytesIO(bites.read()),
                        attachment_filename=name
                )

    if "sidebar.md" in url:
        res =  ds.sidebar_get(url, base_url=base_url)
        if res == None:
            raise RuntimeError("sidebar did not return result")
        return res
    else:            
        doc = ds.doc_get(parts,die=False)
        if doc:
            return doc.dynamic_process(url=request.url)

    return render_template('error_notfound.html',url=url)


