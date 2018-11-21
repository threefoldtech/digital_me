# DigitalMe on Ubuntu 18.04 container

Using following commands you can run the Digital Me on a Ubuntu Server.

## Install dependencies & Jumpscale
```
apt update

apt install -y curl sudo python3 build-essential net-tools

export JUMPSCALEBRANCH="development_960"

curl https://raw.githubusercontent.com/threefoldtech/jumpscale_core/$JUMPSCALEBRANCH/install.sh?$RANDOM > /tmp/install_jumpscale.sh;bash /tmp/install_jumpscale.sh
```
## Start JS shell and build ZDB
```
js_shell

j.servers.zdb.build()

exit
```

## Install Locales packages
You also need the Ubuntu locales packages

````
apt install locales
sudo locale-gen en_US en_US.UTF-8
sudo update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8
export LC_ALL="en_US.UTF-8"
````

## Generate SSH key
To connect to Github you need an SSH key, if you don't have one generate one now:
``` 
ssh-keygen -t rsa
```
You have to add the key in ~/.ssh/id_rsa.pub to your Github account.

## Install & Start Digital me
```
cd code/github/threefoldtech/digital_me

sh install.sh

js_shell 'j.servers.digitalme.start()'
```
You need to answer some questions and the digitalme should be reachable on http://{yourip}:8000

