set -ex


if [ "$(uname)" == "Darwin" ]; then
    echo 'darwin'
    brew install capnp --upgrade
elif [ "$(expr substr $(uname -s) 1 5)" == "Linux" ]; then
    echo "linux"
fi


pip3 install flask_sockets html2text 

pip3 install -e .


python3 -c "from jumpscale import j;j.servers.zdb.build()"
python3 -c "from jumpscale import j;j.tools.jsloader.generate()"
