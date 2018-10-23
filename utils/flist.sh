#!/bin/bash
set -ex

# make output directory
ARCHIVE=/tmp/archives
FLIST=/tmp/flist
mkdir -p $ARCHIVE

# install system deps
apt-get update
apt-get install -y locales git wget netcat tar sudo tmux ssh python3-pip redis-server libffi-dev python3-dev libssl-dev libpython3-dev libssh-dev libsnappy-dev build-essential pkg-config libvirt-dev libsqlite3-dev -y

# setting up locales
if ! grep -q ^en_US /etc/locale.gen; then
    echo "en_US.UTF-8 UTF-8" >> /etc/locale.gen
    locale-gen en_US.UTF-8
    export LC_ALL=en_US.UTF-8
    export LANG=en_US.UTF-8
    export LANGUAGE=en_US.UTF-8

fi

for target in /usr/local $HOME/opt $HOME/.ssh $HOME/opt/cfg $HOME/opt/bin $HOME/code $HOME/code/github $HOME/code/github/threefoldtech $HOME/code/github/threefoldtech/jumpscale_weblibs $HOME/opt/var/capnp $HOME/opt/var/log $HOME/jumpscale/cfg; do
    mkdir -p $target
    sudo chown -R $USER:$USER $target
done

pushd $HOME/code/github/threefoldtech

# cloning source code
for target in jumpscale_core jumpscale_lib jumpscale_prefab digital_me jumpscale_weblibs; do
    git clone https://github.com/threefoldtech/${target}
done

# install jumpscale
for target in jumpscale_core jumpscale_lib jumpscale_prefab digital_me ; do
    cd $HOME/code/github/threefoldtech/${target}
    git checkout development_simple
    pip3 install -e .

done

#ssh generate
ssh-keygen -f ~/.ssh/id_rsa -P ''
eval `ssh-agent -s`
ssh-add ~/.ssh/id_rsa
# initialize jumpscale config manager
mkdir -p $HOME/code/config_test
git init $HOME/code/config_test
touch $HOME/code/config_test/.jsconfig
js_config init --silent --path $HOME/code/config_test/ --key ~/.ssh/id_rsa

redis-server --daemonize yes
js_shell "j.servers.zdb.build()"
js_shell "j.clients.zdb.testdb_server_start_client_get() "
js_shell "j.tools.tmux.execute('js_shell \'j.servers.digitalme.start()\'')"

echo "Waiting digitalme to launch on 8000..."
while ! nc -z localhost 8000; do   
  sleep 10 # wait for 10 seconds before check again
done

cp utils/startup.toml /.startup.toml
tar -cpzf "/tmp/archives/jumpscale_simple.tar.gz" --exclude tmp --exclude dev --exclude sys --exclude proc  /
