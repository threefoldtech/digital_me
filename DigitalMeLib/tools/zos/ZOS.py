from Jumpscale import j
from .ZOSContainer import ZOSContainer
JSBASE = j.application.JSBaseClass

class ZOS(JSBASE):

    def __init__(self,name,data):
        JSBASE.__init__(self)
        self.__dict__.update(data)
        self.name = name


        if j.data.types.bool.clean(self.isvbox):
            self.isvbox = True
            def do():
                return j.tools.zos._exec("container sshinfo").strip().split("\n")[-1]
            self._sshinfo = self._cache.get("sshinfo", method=do, expire=3600, refresh=False, retry=2, die=True)
            self.address = self._sshinfo.split("@")[1].split(" ")[0].strip()
            self.port = int(self._sshinfo.split(" ")[-1])
        else:
            self.isvbox = False
            j.shell()


    @property
    def container_list_data(self):
        def do():
            return j.tools.zos._cmd("container list")
        return self._cache.get("container_list_data", method=do, expire=3600, refresh=False, retry=2, die=True)

    @property
    def container_last_data(self):
        return self.container_list_data[-1]

    @property
    def container_list_hr(self):
        return j.data.serializers.yaml.dumps(self.container_list_data)

    # @property
    # def _containerlist(self):
    #     return [item["name"] for item in self.list_data]

    def container_get(self,name=""):
        if name=="":
            data=self.container_list_data
            tofind = "%s:22"%self.port
            for item in data:
                if "ports" in item:
                     ports = item["ports"]

                if ports.find(tofind)!=-1:
                    data = item
        else:
            for item in self.container_list_data:
                if item["name"]==name:
                    data=item
        return ZOSContainer(zos=self,data=data)

