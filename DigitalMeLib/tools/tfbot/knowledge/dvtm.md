
to build on osx

http://www.brain-dump.org/projects/dvtm/dvtm-0.15.tar.gz

```

brew install ncurses
export PATH="/usr/local/opt/ncurses/bin":$PATH
export LDFLAGS="-L/usr/local/opt/ncurses/lib"
export CPPFLAGS="-I/usr/local/opt/ncurses/include"

CFLAGS=-D_DARWIN_C_SOURCE make

```


https://www.mankier.com/1/abduco

