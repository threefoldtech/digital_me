from Jumpscale import j


SCHEMA="""
@url = jumpscale.bcdb.acl.1
groups = (LO) !jumpscale.bcdb.acl.group
users = (LO) !jumpscale.bcdb.acl.user
hash* = ""

@url = jumpscale.bcdb.acl.group
uid= 4294967295 (I)
rights = ""

@url = jumpscale.bcdb.acl.user
uid= 4294967295 (I)
rights = ""

"""

import types

MODEL_CLASS=j.data.bcdb.latest.model_class_get_from_schema(SCHEMA)


#METHODS WE WILL DYNAMICALLY ADD TO THE OBJECT ITSELF



class ACL(MODEL_CLASS):
    def __init__(self, bcdb):

        MODEL_CLASS.__init__(self, bcdb=bcdb)


    def user_rights_set(self,acl,user,rights="r"):
        if j.data.types.list.check(user):
            for item in user:
                acl.user_rights_set(item,rights)
        else:
            if user in acl._ddict["groups"]:
                j.shell()

    def user_rights_check(self,acl,userid,rights):
        res=True
        for right in rights:
            res = acl.user_right_check(userid,right) and right
        return res

    def user_right_check(self,acl,userid,right):
        j.shell()


    def _methods_add(self,obj):
        obj.user_rights_set = types.MethodType(self.user_rights_set,obj)
        obj.user_rights_check = types.MethodType(self.user_rights_check,obj)
        obj.user_right_check = types.MethodType(self.user_right_check,obj)
        return obj

    def _dict_process_out(self,d):
        res={}
        print(d)
        for group in d["groups"]:
            r=j.data.types.list.clean(group["rights"])
            r="".join(r)
            res[group["uid"]]=r #as string
        d["groups"]=res
        res={}
        for user in d["users"]:
            r=j.data.types.list.clean(user["rights"])
            r="".join(r)
            res[user["uid"]]=r #as string
        d["users"]=res
        return d

    def _set_pre(self,acl):
        """
        will serialize the acl in a very specific sorted way to make sure we can calculate the hash

        :param acl:
        :return:
        """
        acl.hash=j.data.hash.md5_string(acl._json)

        res = self.index.select().where(self.index.hash == acl.hash).first()
        if res:
            #means this acl already exists, need to return the id of the one already saved
            acl.id = res.id
            w=self.get(acl.id)
            if w is None:
                self.index_rebuild()
                acl.id = None
                return True,acl
            return False,acl #no need to save

        return True,acl


