from Jumpscale import j
JSBASE = j.application.JSBaseClass

class CapacityPlanner(JSBASE):

    def __init__(self):
        JSBASE.__init__(self)

    def vm_reserve(self,node, name, mem=1,cores=1):
        """
        reserve on node (node model obj) a vm
        :param mem:
        :param cores:
        :return:
        """

        #question: is there a name we can give to a vm

        #the node robot should send email to the 3bot email address with the right info (access info)

        #for now we store the secret into the reservation table so also this farmer robot can do everything
        ## in future this will not be the case !!!

        #need to use zero-node robot to create the reservation

        #question: what are the other parameters

        pass

        #TODO:*1

    def vm_delete(self,node,name, namespacename):
        pass

        # TODO:*1

    def zdb_reserve(self, node, namespacename, size=100, secret="", ):
        """

        :param node: is the node obj from model
        :param size:  in MB
        :param secret: secret to be given to the namespace
        :param namespacename: cannot exist yet
        :return:
        """

        pass

        # TODO:*1
        #are there other params?

    def zdb_delete(self,node,namespacename):
        pass
        # TODO:*1

    #DO SAME FOR GATEWAY