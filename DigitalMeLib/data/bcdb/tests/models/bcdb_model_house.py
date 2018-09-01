
from jumpscale import j
JSBASE = j.application.jsbase_get_class()

SCHEMA = """
@url = jumpscale.bcdb.test.house2
@name = test_house
name = "" (S)
active = "" (B)
cost = (N)
room = (LO) !jumpscale.bcdb.test.room2

@url = jumpscale.bcdb.test.room2
@name = test_room
name = "" (S)
active = "" (B)
colors = []

"""

MODEL_CLASS = j.data.bcdb.MODEL_CLASS
class Model(MODEL_CLASS):

    def __init__(self,bcdb=None):
        MODEL_CLASS.__init__(self, bcdb=bcdb, schema=SCHEMA)

    def _init(self):
        j.shell()



