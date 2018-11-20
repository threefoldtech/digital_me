import os
from Jumpscale import j
from .flist import HubFlist, HubPublicFlist

class HubMerger:
    def __init__(self, config, username, flistname):
        self.config = config
        self.destination = HubPublicFlist(config, username, flistname)

        # ensure user exists
        self.destination.user_create()

    def merge(self, sources):
        items = {}
        merger = j.tools.flist.get_merger()

        # extracting flists to distinct directories
        for source in sources:
            flistpath = os.path.join(self.config['public-directory'], source)

            if not os.path.exists(flistpath):
                return "%s source doesn't exists" % source

            flist = HubFlist(self.config)
            flist.loads(flistpath)
            merger.add_source(flist.flist)

            items[source] = flist

        # merging sources
        self.destination.raw.initialize("/")
        merger.add_destination(self.destination.raw.flist)
        merger.merge()

        self.destination.raw.commit()
        self.destination.raw.pack(self.destination.target)

        return True
