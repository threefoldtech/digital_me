from Jumpscale import j


JSBASE = j.application.JSBaseClass


class packages(JSBASE):
    """Actor for managing digital me packages
    """

    def add(self, path):
        """
        ```in
        path = "" (S)
        ```
        Add package located at path to digitalme

        :param path: the path of the package, it can be the github url or the local path
        :type path: string
        """
        j.servers.digitalme.package_add(path)
