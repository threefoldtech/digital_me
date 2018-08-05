from blueprints.wiki import blueprint
from flask import render_template, send_file
from flask import abort, redirect, url_for

import io

# from flask_login import login_required

from werkzeug.routing import BaseConverter
from jumpscale import j


@blueprint.route('/index')
@blueprint.route('/')
def index():
    return redirect("wiki/foundation")


@blueprint.route('')
def index_sub(sub):
    return render_template('index_docsify.html')


@blueprint.route('/<path:subpath>')
def wiki_route(subpath):
    
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


    if len(parts)>0 and parts[0]=="verify":
        res =  verify(wikicat)

    try:
        #at this point we know the docsite

        ds = j.tools.markdowndocs.docsite_get(wikicat)

        #if binary file, return
        name = parts[-1]
        if not name.endswith(".md"):
            file_path = ds.file_get(name)
            with open(file_path, 'rb') as bites:
                return send_file(
                            io.BytesIO(bites.read()),
                            attachment_filename=name
                    )                

    except Exception as e:
        raise e
        return ("# **ERROR**\n%s\n"%e)

    if "sidebar.md" in url:
        return ds.sidebar_get(url)
    else:            
        doc = ds.doc_get(parts,die=False)
        if doc:
            return doc.markdown

    return render_template('error_notfound.html',url=url)


def verify(wikicat):
    ds = j.tools.markdowndocs.docsite_get(wikicat)
    return ds.verify()
