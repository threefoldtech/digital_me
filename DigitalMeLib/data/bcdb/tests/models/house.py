
from jumpscale import j
JSBASE = j.application.jsbase_get_class()

SCHEMA = """
@url = jumpscale.bcdb.test.house
@name = test_house
name = "" (S)
active = "" (B)
cost = (N)
room = (LO) !jumpscale.bcdb.test.room

@url = jumpscale.bcdb.test.room
@name = test_room
name = "" (S)
active = "" (B)
colors = []

"""

class Model(j.data.bcdb.MODEL_CLASS):

    def _init(self):
        pass



