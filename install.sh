set -ex


if [ "$(uname)" == "Darwin" ]; then
    echo 'darwin'
    brew install capnp --upgrade
    CFLAGS="-mmacosx-version-min=10.7 -std=c++11 -stdlib=libc++" pip3 install pycapnp
elif [ "$(expr substr $(uname -s) 1 5)" == "Linux" ]; then
    echo "linux"
fi


pip3 install flask_sockets html2text pyblake2 flask_login flask_sqlalchemy gipc

pip3 install -e .


python3 -c "from Jumpscale import j;j.servers.zdb.build()"
python3 -c "from Jumpscale import j;j.tools.jsloader.generate()"
