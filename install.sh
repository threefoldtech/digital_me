set -ex
sudo apt install libssl-dev
python3 -c "from jumpscale import j;j.servers.zdb.build()"
python3 -c "from jumpscale import j;j.tools.jsloader.generate()"
