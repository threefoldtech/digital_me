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
    locale-gen
fi

for target in /usr/local $HOME/opt $HOME/opt/cfg $HOME/opt/code $HOME/opt/code/github $HOME/opt/code/github/threefoldtech $HOME/opt/var/capnp $HOME/opt/var/log $HOME/jumpscale/cfg; do
    mkdir -p $target
    sudo chown -R $USER:$USER $target
done


for target in /usr/local $HOME/opt $HOME/opt/cfg $HOME/opt/code $HOME/opt/code/github $HOME/opt/code/github/threefoldtech $HOME/opt/var/capnp $HOME/opt/var/log $HOME/jumpscale/cfg; do
    mkdir -p $target
    sudo chown -R $USER:$USER $target
done

pushd $HOME/opt/code/github/threefoldtech

# cloning source code

export JUMPSCALEBRANCH="development_simple"
curl https://raw.githubusercontent.com/threefoldtech/jumpscale_core/$JUMPSCALEBRANCH/install.sh?$RANDOM > /tmp/install_jumpscale.sh;bash /tmp/install_jumpscale.sh
# install jumpscale
for target in jumpscale_core jumpscale_lib jumpscale_prefab digital_me ; do
    cd $HOME/opt/code/github/threefoldtech/${target}
    pip3 install -e .

done

tar -cpzf "/tmp/archives/jumpscale_simple.tar.gz" --exclude tmp --exclude dev --exclude sys --exclude proc  /
