set -ex
#sudo apt install libssl-dev
pip3 install flask_sockets html2text 

pip3 install -e .


python3 -c "from jumpscale import j;j.servers.zdb.build()"
python3 -c "from jumpscale import j;j.tools.jsloader.generate()"
