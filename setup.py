from setuptools import setup, find_packages
from setuptools.command.install import install as _install
from setuptools.command.develop import develop as _develop
import os



def _post_install(libname, libpath):
    from Jumpscale import j
    # add this plugin to the config
    c = j.core.state.configGet('plugins', defval={})
    c[libname] = "%s/github/threefoldtech/digital_me/DigitalMeLib" % j.dirs.CODEDIR
    # c[libname] = libpath
    j.core.state.configSet('plugins', c)
    j.tools.jsloader.generate()


class install(_install):

    def run(self):
        _install.run(self)
        libname = self.config_vars['dist_name']
        libpath = os.path.join(os.path.dirname(
            os.path.abspath(__file__)), libname)
        self.execute(_post_install, (libname, libpath),
                     msg="Running post install task")


class develop(_develop):

    def run(self):
        _develop.run(self)
        libname = self.config_vars['dist_name']
        libpath = os.path.join(os.path.dirname(
            os.path.abspath(__file__)), libname)
        self.execute(_post_install, (libname, libpath),
                     msg="Running post install task")


long_description = ""
try:
    from pypandoc import convert
    long_description = convert('README.md', 'rst')
except ImportError:
    long_description = ""


setup(
    name='DigitalMeLib',
    version='9.4.0-rc4',
    description='Framework behind digitalme',
    long_description=long_description,
    url='https://github.com/Jumpscale/lib',
    author='ThreeFoldTech',
    author_email='info@threefold.tech',
    license='Apache',
    packages=find_packages(),
    install_requires=[
        'Jinja2>=2.9.6',
        'Jumpscale>=9.4.0-rc4',
        'Jumpscale>=9.4.0-rc4',
        'gevent>=1.2.1',
        'grequests>=0.3.0',
        'peewee>=2.9.2',
        'pudb>=2017.1.2',
        'pycapnp>=0.5.12',
        'redis>=2.10.5',
        'requests>=2.13.0',
        'toml>=0.9.2',
        'watchdog>=0.8.3',
        'dnspython>=1.15.0',
        'zerotier>=1.1.2',
        'blosc>=1.5.1',
        'pynacl>=1.1.2',
        'ipcalc>=1.99.0',
        'ed25519>=1.4',
        'python-jose>=1.3.2',
        'g8storclient',
        'gipc',
        'rq-dashboard',
        'cryptocompare'
    ],
    cmdclass={
        'install': install,
        'develop': develop,
        'developement': develop,
    },
)
