# packages

## Intro

are directories which can be added as a packaged to digital.me.
The metadata of a package is stored in a complex type.

in the root of a package dir there can be a toml file
name should be dm_config.toml

## types:

are subdirs of a package

- actors
    - is the logic inside a package
    - the code inside an actor should call as much as possible libraries in jumpscale (sals, clients, ...)
    - is also the implementation of our api for this package to the outside world, our interface basically
        - published under:  $locationdm/$packagename/api/$restmethods (TO BE IMPLEMENTED)
    - also published in gedis under $packagename
- blueprint(s)
    - flask blueprint, is the webserver part
    - if plural (ends with s) then subdirs are the individual blueprint(s) = instances
      otherwise is blueprint_$name if only blueprint then is name of package
- chatflows
    - interactive communication, implemented as chat bots
- schemas
    - the models used in a package, is j.data.schema ...
- docsite & docsites
    - if plural (ends with s) then subdirs are the individual docsite(s) = instances
    - markdown documentation sites, published underneith /wiki/$docsite_prefix/...
    - otherwise is docsite_$name
- docmacros
    - macro's as used in docsite(s)
- zrobot_repo
    - path or url for zerorobot
- configobjects
    - configuration objects which are serialized as yaml or toml or json
    - get loaded in BCDB for this DigitalME


## schema used to store a package metadata

see

```
!!!include(
        name="Package.py",start_include=False,end_include=False
        giturl="https://raw.githubusercontent.com/threefoldtech/digital_me/{{JS9_BRANCH}}/DigitalMeLib/servers/digitalme",
        start="SCHEMA_PACKAGE",
        end="##ENDSCHEMA",
        )
```


## Example TOML

also explains what the meaning is of the metadata entries in the config format

```
!!!include(name="package.toml")
```
