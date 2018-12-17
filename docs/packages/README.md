# Packages

## Intro

A package is functionality being added to digitalme.

When digitalme starts, it loads the packages `digitalme_base` and `digitalme_chat`.

`digitalme_chat` can be used to communicate with chatbots added through chatflows as discussed [below](#chatflows).

`digitalme_base` can be used to add packages dynamically when digitalme is already running.

```
redis-cli -h  localhost -p 8001
localhost:8001> digitalme_base.packages.add '{"path":"/root/code/github/threefoldtech/digital_me/packages/system/example/"}'
```


## Package local location

A package is loaded locally in the following location, where `$PACKAGENAME` is the name of the package defined in the package configuration.

- j.dirs.VARDIR + "dm_packages" + $PACKAGENAME

## Package confgiuration

A package is expected to contain configuration file `dm_package.toml` otherwise it will fail to load.

This an example of a package configuration file:
```
name = "digitalme_base" #unique name for the package
enable = true

[[loaders]]
giturl = "https://github.com/threefoldtech/digital_me/tree/{{JS_BRANCH}}/packages/system/base"
dest = ""

[[loaders]]
giturl = "https://github.com/threefoldtech/jumpscale_weblibs/tree/master/static"
dest = "blueprints/base/static"


[[args]]
key = "JS_BRANCH"
val = "development_960"
```

- `name` : the name that will be used locally for this package. This name will be used for creating a directory for the package under `j.dirs.VARDIR + "dm_packages"` and for executing actor commands from this package. The name shouldn't contain `.` because Gedis splits on `.`.
 - `enabled`: boolean indicating if this package will be enabled/disabled after loading it into digitalme.
 - `loaders`: a configuration to load files from git urls to this package. A package needs at least one loaders section, otherwise the local package will be empty.
 - `args`: key/val args used to replace variables in the loaders using jinja2.

### loaders

When the package class is loading a package, it starts by symlinking the package dirs into the local package directory. The packages dirs to be symlinked are determined by the loaders mentioned above not by the dirs in the remote package.

If a `loaders` section has a `dest` value, the remote directory will be cloned and symlinked to this destination under the local package path.

If a `loaders` section doesn't have a `dest` value, the package loader will check the remote directory for the package subdirectories discussed below, and links them locally if it finds any.

For example, loading a package with the confiugration above, will result in the following directory structure.

```
root@wonderwoman:~/opt/var/dm_packages# tree digitalme_base/
digitalme_base/
├── actors
│   ├── packages.py -> /root/code/github/threefoldtech/digital_me/packages/system/base/actors/packages.py
│   └── __pycache__
│       └── packages.cpython-36.pyc
└── blueprints
    └── base
        └── static -> /root/code/github/threefoldtech/jumpscale_weblibs/static
```

## Package Subdirectories:

are subdirs of a package that can be processed by digitalme to offer a certain functionality.

### actors

The actors hold the package logic in the form of commands. Each file is an actor and is expected to contain a class with the same name.
Each function in this class is a command that will be published under namespace $packagename.

The package loader symlinks files in the remote actors dir to the local dir, but it doesn't symlink and load files in sub
directories.

The code inside an actor should use jumpscale libraries as much as possible.


This is an example of an actor file contaiing one command `ping`:

```
from Jumpscale import j


JSBASE = j.application.JSBaseClass


class example(JSBASE):

    def ping(self):
        return 'PONG'
```

If this actor is part of package `digitalme_example`, you can execute the `ping` command using a redis-cli:

```
redis-cli -h  localhost -p 8001
localhost:8001> digitalme_example.example.ping
PONG
```


### chatflows

Each file is a chatbot used to implement interactive communication.
The file is expected to contain a function `chat` with takes argument `bot`.
The package loader symlinks files in the remote actors dir to the local dir, but it doesn't symlink and load files in sub
directories.

This is an example of a chatflow called `food_get`:

```
from Jumpscale import j

def chat(bot):
    res = {}
    food = bot.string_ask("What do you need to eat?")
    amount = bot.int_ask("Enter the amount you need to eat from %s in grams:" % food)
```

to communicate with this bot using the redis protocol, you can use the the `chat` package and start a new session with this bot.

```
localhost:8001> digitalme_chat.chatbot.session_new '{"topic":"food_get"}'
"{\n \"session_id\": \"6fcdc9ee-2aeb-473f-945a-8d99053354c0\"\n}"
localhost:8001> digitalme_chat.chatbot.work_get '{"session_id":"6fcdc9ee-2aeb-473f-945a-8d99053354c0"}'
"{\n\"cat\": \"string_ask\",\n\"msg\": \"What do you need to eat?\",\n\"kwargs\": {}\n}"
localhost:8001> digitalme_chat.chatbot.work_report '{"session_id":"6fcdc9ee-2aeb-473f-945a-8d99053354c0", "result":"Chicken"}'
(nil)
localhost:8001> digitalme_chat.chatbot.work_get '{"session_id":"6fcdc9ee-2aeb-473f-945a-8d99053354c0"}'
"{\n\"cat\": \"int_ask\",\n\"msg\": \"Enter the amount you need to eat from Chicken in grams:\",\n\"kwargs\": {}\n}"
localhost:8001> digitalme_chat.chatbot.work_report '{"session_id":"6fcdc9ee-2aeb-473f-945a-8d99053354c0", "result":50}'
(nil)
```

### schemas

Schemas is where you define models used in this package.
Each file is a schema that can be processed by `j.data.schema`
The package loader loads the schema in gedis and adds it to the bcdb instance of the package.
The package loader symlinks files in the remote actors dir to the local dir, but it doesn't symlink and load files in sub
directories.


### docsites

Docesites are markdown documentation sites, published under /wiki/$docsite_prefix/..
The package loader expects the remote docsites to have sub dirs and symlinks files in those sub dirs, where each sub dir
is a docsite.


### docmacros

Macros used in the docsites. Each file inside is a docmacro.
The package loader symlinks files in the remote actors dir to the local dir, but it doesn't symlink and load files in sub
directories.


### zrobotrepos
N/A

### web

openresty configurations for this packages


###recipes:
N/A


