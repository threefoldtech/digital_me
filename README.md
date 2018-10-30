# digital_me

## Installation:

*** Digital me depends on Jumpscale, so make sure that you have installed [Jumpscale](https://github.com/threefoldtech/jumpscale_core) before.
```bash
cd /opt/code/github/threefoldtech/
git clone https://github.com/threefoldtech/digital_me.git
cd digital_me 
bash install.sh
```

### Running

you can run Digital_me using `js_shell`
```bash
js_shell 'j.servers.digitalme.start()'
```

### Packages

DigitalMe already have some basic packages like (orderbook, dm_base, ..etc). 
DigitalMe package must contain `dm_config.toml` file which contains some info about the package and can be enabled from there.

The [package loader](https://github.com/threefoldtech/digital_me/blob/development_960/DigitalMeLib/servers/digitalme/Package.py)
tries to load from directories (gedis `actors`, flask `blueprints`, `chatflows`, zdb `models`, ....etc) 
and use `dm_config.toml` also to load extra data.
