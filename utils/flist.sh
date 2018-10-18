#!/bin/bash

set -ex

# make output directory
ARCHIVE=/tmp/archives
FLIST=/tmp/flist
mkdir -p $ARCHIVE

# install system deps (done)
apt-get update
apt-get install -y locales git sudo python3-pip libffi-dev python3-dev libssl-dev libpython3-dev libssh-dev libsnappy-dev build-essential pkg-config libvirt-dev libsqlite3-dev -y

# setting up locales
if ! grep -q ^en_US /etc/locale.gen; then
    echo "en_US.UTF-8 UTF-8" >> /etc/locale.gen
    locale-gen en_US.UTF-8
fi

for target in /usr/local $HOME/opt $HOME/opt/cfg $HOME/opt/bin $HOME/code $HOME/code/github $HOME/code/github/threefoldtech $HOME/opt/var/capnp $HOME/opt/var/log $HOME/jumpscale/cfg; do
    mkdir -p $target
    sudo chown -R $USER:$USER $target
done

pushd $HOME/code/github/threefoldtech

# cloning source code

for target in jumpscale_core jumpscale_lib jumpscale_prefab digital_me; do
    git clone https://github.com/threefoldtech/${target}
done

# install jumpscale
for target in jumpscale_core jumpscale_lib jumpscale_prefab digital_me ; do
    cd $HOME/code/github/threefoldtech/${target}
    git checkout development_simple
    pip3 install -e .

done

wget http://download.redis.io/redis-stable.tar.gz
tar xvzf redis-stable.tar.gz
cd redis-stable
make
service redis-server start
js_shell "j.servers.zdb.build()"
js_shell "j.clients.zdb.testdb_server_start_client_get() "
#try build
tar -cpzf "/tmp/archives/jumpscale_simple.tar.gz" --exclude tmp --exclude dev --exclude sys --exclude proc  /
