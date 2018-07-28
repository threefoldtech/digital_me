set -ex
sudo apt install libssl-dev
python3 -c "from js9 import j;j.servers.zdb.build()"
python3 -c "from js9 import j;j.tools.jsloader.generate()"
