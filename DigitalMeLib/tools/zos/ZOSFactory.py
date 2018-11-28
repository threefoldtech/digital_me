from Jumpscale import j

JSBASE = j.application.JSBaseClass

class ZOSFactory(JSBASE):

    def __init__(self):
        self.__jslocation__ = "j.tools.zos"
        JSBASE.__init__(self)
        self.logger_enable()

        self.code_location_source="/sandbox/code/github/threefoldtech"
        self.code_location_dest="/root/code/github/threefoldtech"
        self._list = []



    def _cmd(self,cmd):
        cmd+=" --json"
        rc,out,err = j.sal.process.execute(cmd)
        data = j.data.serializers.json.loads(out)
        return data

    @property
    def list_data(self):
        data = self._cmd("zos showconfig"):
        j.shell()

    @property
    def list_hr(self):
        return j.data.serializers.yaml.dumps(self.list_data)


    def get(self,name=""):
        """
        get zos object, get the default one if not specified
        :param name:
        :return:
        """

    def test(self):
        """
        js_shell 'j.tools.zos.test()'
        """

        print(self.list_data)
