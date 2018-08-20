# packages

are directories which can be added as a packaged to digital.me.

Each package has following (optional) subdirs

- actors
- blueprint
- chatflows
- schemas
- recipes
- docs
- macros
- configs

there is a dm_config.toml file which has some required info in there

Apart from the subdirectories as specified above digital me will also checkout git repo's as specified in the dependency sections.

```toml

enable = false

[[actors]]
name = 
url = 

[[blueprint]]
publish = "/mysite"
name = "mysite"
url = 
enable = false

[[chatflows]]
name = "mysite"
url = 

[[blueprint_links]]
#needs to correspond with name of blueprint above
#if name not given then is the blueprint directory
name = "mysite" 
url = "https://github.com/threefoldtech/jumpscale_weblibs/tree/master/static"
dest = "static/"
enable = false

[[schemas]]
name = 
url = 


[[recipes]]
name = 
url = 

[[docsite]]
name = "tools"
url = "https://github.com/threefoldfoundation/info_tools/blob/master"
publish = "/tools"


[[doc_macros]]
name = "core9"
url = "https://github.com/threefoldtech/jumpscale_core/tree/development"

[[zrobot_repo]]
name = ""
url = ""

[[config_objects]]
name = ""
url = ""

```

- the prefix is what get's registered on the webserver
- when enable True then its being registered (standard True)


## actors

- is the api to the outside world, our interface basically

## blueprints

- flask blueprints they get registered onto the main server

## chatflows

- are highlevel chat flows, communication with users

## schemas

- jumpscale schema's

## recipe's

- recipes for digitalme for coordinators & services

## docs

- markdown docs 

## doc_macro's

- macro's as they are understood by the docs (markdown)

##  zrobot_repos

- zero-robot repositories
- they get loaded in mem in a zero-robot instance

## configs

- are configuration objects modelled as jumpscale schema's 