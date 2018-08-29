import os
import sys

from flask import Blueprint, jsonify, url_for
from jumpscale import j
from .flask_itsyouonline import configure, callback
from . import settings

name =  j.sal.fs.getDirName(__file__,True)
print("NAME::: ", name)

blueprint = Blueprint(
    '%s_blueprint'%name,
    __name__,
    url_prefix="/%s"%name,
    template_folder='templates',
    static_folder='static'
)

configure(blueprint, settings.IYO_CLIENTID, settings.IYO_SECRET, settings.IYO_CALLBACK, '/gridcapacity/callback', None, True, True, 'organization')

@blueprint.app_template_filter
def uptime(seconds):
    if not seconds:
        return "not available"

    delta = datetime.timedelta(seconds=seconds)

    # manually compute hh:mm:ss
    hrs = int(delta.seconds / 3600)
    min = int((delta.seconds - (hrs * 3600)) / 60)
    sec = delta.seconds % 60

    if delta.days > 0:
        return '%d days, %02d:%02d:%02d' % (delta.days, hrs, min, sec)

    return '%02d:%02d:%02d' % (hrs, min, sec)


@blueprint.app_template_filter
def deltatime_color(time):
    """
    return a color base on the delta time between now and time

    :param time: time we when to compare
    :type time: datetime.datetime
    :return: color
    :rtype: str
    """
    if not time:
        return 'danger'

    delta = (datetime.datetime.now() - time).total_seconds()
    if delta <= 600:  # 10 minutes or less
        return 'success'
    if 600 < delta and delta < 900:  # between 10 and 15 minutes
        return 'warning'
    if delta > 900:  # plus de 15 minutes
        return 'danger'


@blueprint.app_template_filter
def node_status(time):
    """
    return a color base on the delta time between now and time

    :param time: time we when to compare
    :type time: datetime.datetime
    :return: color
    :rtype: str
    """
    if not time:
        return 'down'

    delta = (datetime.datetime.now() - time).total_seconds()
    if delta <= 600:  # 10 minutes or less
        return 'up'
    if 600 < delta and delta < 900:  # between 10 and 15 minutes
        return 'likely down'
    if delta > 900:  # plus de 15 minutes
        return 'down'


@blueprint.errorhandler(500)
def internal_error(err):
    _, _, exc_traceback = sys.exc_info()
    eco = j.core.errorhandler.parsePythonExceptionObject(err, tb=exc_traceback)
    return jsonify(code=500, message=eco.errormessage, stack_trace=eco.traceback), 500

