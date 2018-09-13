import os

from Jumpscale import j

db_client = j.clients.redis_config.get().redis
db = j.data.bcdb.get(db_client)
db.tables_get(os.path.join(os.path.dirname(__file__), 'schemas'))

Location = db.tables['location']
Resources = db.tables['resource']
Capacity = db.tables['capacity']
Farmer = db.tables['farmer']


class NodeRegistration:
    @staticmethod
    def list(country=None):
        """
        list all the capacity, optionally filter per country.
        returns a list of capacity object

        :param country: [description], defaults to None
        :param country: [type], optional
        :return: sequence of Capacity object
        :rtype: sequence
        """

        for capacity in Capacity.find(id='*'):
            if country and capacity.country == country:
                yield capacity

    @staticmethod
    def get(node_id):
        """
        return the capacity for a single node

        :param node_id: unique node ID
        :type node_id: str
        :return: Capacity object
        :rtype: Capacity
        """
        capacity = Capacity.get(id=node_id)
        if not capacity:
            raise NodeNotFoundError("node '%s' not found" % node_id)
        return capacity

    @staticmethod
    def search(country=None, mru=None, cru=None, hru=None, sru=None, farmer=None, ** kwargs):
        """
        search based on country and minimum resource unit available

        :param country: if set, search for capacity in the specified country, defaults to None
        :param country: str, optional
        :param mru: minimal memory resource unit, defaults to None
        :param mru: int, optional
        :param cru: minimal CPU resource unit, defaults to None
        :param cru: int, optional
        :param hru: minimal HDD resource unit, defaults to None
        :param hru: int, optional
        :param sru: minimal SSD resource unit defaults to None
        :param sru: int, optional
        :return: sequence of Capacity object matching the query
        :rtype: sequence
        """

        nodes = []

        for node in Capacity.find(id='*'):
            if country and node.country != country:
                continue

            if farmer and node.farmer.name != farmer:
                continue

            if mru and node.total_resources.mru >= mru:
                continue

            if cru and node.total_resources.cru >= cru:
                continue

            if hru and node.total_resources.hru >= hru:
                continue

            if sru and node.total_resources.sru >= sru:
                continue

            nodes.append(node)

        if kwargs.get('order'):
            key = kwargs.get('order')
            nodes = nodes.sort(key = lambda o:getattr(o, key))

        page = kwargs.get('page')
        per_page = kwargs.get('per_page', 50)
        if page:
            start = (page - 1) * per_page
            end = start + per_page
            if nodes:
                return nodes[start:end]

        return nodes

    @staticmethod
    def all_countries():
        """
        yield all the country present in the database

        :return: sequence of country
        :rtype: sequence of string
        """
        capacities = Capacity.find(id="*")
        countries = set()
        for cap in capacities:
            if cap.location:
                countries.add(cap.location.country)
        return list(countries)


class FarmerRegistration:

    @staticmethod
    def create(name, iyo_account, wallet_addresses=None):
        f = Farmer.new()
        f.name = name
        f.iyo_account = iyo_account
        f.wallet_addresses = wallet_addresses
        return f

    @staticmethod
    def register(farmer):
        if farmer.schema.url != Farmer.schema.url:
            raise TypeError("farmer need to be a Farmer object, not %s" % type(farmer))
        Farmer.set(farmer)

    @staticmethod
    def list(name=None, organization=None, **kwargs):

        farmers = []

        for farmer in Farmer.find(id='*'):
            if name and farmer.name != name:
                continue

            if organization and farmer.iyo_organization != organization:
                continue

            farmers.append(farmer)

        # sorting
        key = kwargs.get('order')
        if key:
            farmers.sort(key = lambda o:getattr(o, key))
        return farmers

    @staticmethod
    def get(id):
        farmer = Farmer.get(id=id)
        if not farmer:
            raise FarmerNotFoundError("farmer '%s' not found" % id)
        return farmer

class FarmerNotFoundError(KeyError):
    pass


class NodeNotFoundError(KeyError):
    pass
