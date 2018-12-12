from Jumpscale import j
from .ZOSContainer import ZOSContainer
JSBASE = j.application.JSBaseClass

class ZOS(JSBASE):

    def __init__(self,name,data):
        self.__dict__.update(data)
        self.name = name
        self._list = []

        if j.data.types.bool.clean(self.isvbox):
            self.isvbox = True
            t = j.tools.zos._exec("container sshinfo").strip().split("\n")[-1]
            self.address = t.split("@")[1].split(" ")[0].strip()
        else:
            self.isvbox = False
            j.shell()

    @property
    def container_list_data(self):
        if self._list == []:
            self._list = j.tools.zos._cmd("container list")
        return self._list

    @property
    def container_last_data(self):
        return self.container_list_data[-1]

    @property
    def container_list_hr(self):
        return j.data.serializers.yaml.dumps(self.container_list_data)

    @property
    def _containerlist(self):
        return [item["name"] for item in self.list_data]

    def container_get(self,name="kds3"):
        if name=="":
            data=self.container_last_data
        else:
            for item in self.container_list_data:
                if item["name"]==name:
                    data=item
        return ZOSContainer(zos=self,data=data)

