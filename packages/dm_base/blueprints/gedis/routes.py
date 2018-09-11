from flask import render_template, redirect, request, url_for
from blueprints.gedis import *
from Jumpscale import j
import gevent

login_manager = j.servers.web.latest.loader.login_manager
from gevent import time


#alias for scheduling rq job
schedule = j.servers.gedis.latest.job_schedule

users = [
    {"id": 1, "name": "ahmed", "email": "ahmed@dmdm.com"},
]
todos = [
    {"id": 1, "title": "fix it", "done": False},
]

@blueprint.route('/')
def route_default():
    return redirect('/%s/gedis_index.html'%name)


def test2(timetowait=20,descr="should not be visible"):
    print("TEST2:%s"%descr)
    import time
    time.sleep(timetowait)
    return descr



@blueprint.route('/test')
def gedis_test():
    greenlets=[]
    for i in range(10):
        job = schedule(test2,timetowait=i,descr="HELLO",timeout=60)
        greenlets.append(job.greenlet)
    print("START")
    gevent.joinall(greenlets)
    print("STOP")
    return "ALLDONE"
    # res=schedule(test2,wait=True,timetowait=3,descr="HELLO")

@blueprint.route('/admin')
def route_admin():
    # needs to return the session id
    models2datatable = {
        'user': {
            "view": "datatable",
            "id": "crudPanel",
            "icon": "user",
            "columns": [
                {"id": "id"},
                {"id": "name"},
                {"id": "email"},
            ],
            "data": users,
        },
        'todo': {
            "view": "datatable",
            "id": "crudPanel",
            "icon": "dashboard",
            "columns": [
                {"id": "id"},
                {"id": "title"},
                {"id": "done"},
                {"id": "notes"},
            ],
            "data": todos,

        }
    }
    return render_template("gedis_admin.html", data=models2datatable)



# @login_required
@blueprint.route('/<template>')
def route_template(template):
    return render_template(template)


