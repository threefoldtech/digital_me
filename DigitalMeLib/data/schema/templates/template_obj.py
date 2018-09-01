from Jumpscale import j

List0=j.data.schema.list_base_class_get()

class ModelOBJ():
    
    def __init__(self,schema,data={}, capnpbin=None):
        self._schema = schema
        self._capnp_schema = schema.capnp_schema

        self._changed_list = False
        self._changed_prop = False
        self._changed_items = {}

        if capnpbin != None:
            self.__cobj = self._capnp_schema.from_bytes_packed(capnpbin)
        else:
            self.__cobj = self._capnp_schema.new_message()



        {# list not as property#}
        {% for ll in obj.lists %}    
        self.{{ll.alias}} = List0(self,self._cobj.{{ll.name_camel}}, self._schema.property_{{ll.name}})
        {% endfor %}

        self._JSOBJ = True

        self.id = None
        self._changed_prop_permanent = False
        {% for prop in obj.properties %}
        {% if prop.jumpscaletype.NAME == "jsobject" %}
        self._schema_{{prop.name}} = j.data.schema.schema_get(url="{{prop.jumpscaletype.SUBTYPE}}")
        self._changed_prop = True
        self._changed_prop_permanent = True
        if self._cobj.{{prop.name_camel}}:
            self._changed_items["{{prop.name_camel}}"] = self._schema_{{prop.name}}.get(capnpbin=self._cobj.{{prop.name_camel}})
        else:
            self._changed_items["{{prop.name_camel}}"] = self._schema_{{prop.name}}.new()         
        {% endif %} 
        {% endfor %}


        for key,val in data.items():
            setattr(self, key, val)


    {# generate the properties #}
    {% for prop in obj.properties %}
    @property 
    def {{prop.alias}}(self):
        {% if prop.comment != "" %}
        '''
        {{prop.comment}}
        '''
        {% endif %} 
        {% if prop.jumpscaletype.NAME == "jsobject" %}
        return self._changed_items["{{prop.name_camel}}"]
        {% else %} 
        if self._changed_prop and "{{prop.name_camel}}" in self._changed_items:
            return self._changed_items["{{prop.name_camel}}"]
        else:
            return self._cobj.{{prop.name_camel}}
        {% endif %} 
        
    @{{prop.alias}}.setter
    def {{prop.alias}}(self,val):
        {% if prop.jumpscaletype.NAME == "jsobject" %}
        self._changed_items["{{prop.name_camel}}"] = val
        {% else %} 
        #will make sure that the input args are put in right format
        val = {{prop.js_typelocation}}.clean(val)  #is important because needs to come in right format e.g. binary for numeric
        if self.{{prop.alias}} != val:
            self._changed_prop = True
            self._changed_items["{{prop.name_camel}}"] = val
        {% endif %} 

    {% if prop.jumpscaletype.NAME == "numeric" %}
    @property 
    def {{prop.alias}}_usd(self):
        # return self.{{prop.alias}}_cur('usd')
        return {{prop.js_typelocation}}.bytes2cur(self.{{prop.alias}})

    @property 
    def {{prop.alias}}_eur(self):
        # return self.{{prop.alias}}_cur('eur')
        return {{prop.js_typelocation}}.bytes2cur(self.{{prop.alias}},curcode="eur")

    def {{prop.alias}}_cur(self,curcode):
        """
        @PARAM curcode e.g. usd, eur, egp, ...
        """
        return {{prop.js_typelocation}}.bytes2cur(self.{{prop.alias}}, curcode = curcode)
        # # cannot pass in string to bytes2cur, have to encode into packed first
        # strval = self.{{prop.alias}}
        # if isinstance(strval, bytes):
        #     strval = strval.decode()
        # binval = {{prop.js_typelocation}}.str2bytes(strval)
        # return {{prop.js_typelocation}}.bytes2cur(binval,curcode=curcode)
    {% endif %}

    {% endfor %}

    def _check(self):
        #checks are done while creating ddict, so can reuse that
        self._ddict
        return True

    @property
    def _cobj(self):
        if self._changed_list or self._changed_prop:
            # print("go inside cobj")
            ddict = self.__cobj.to_dict()

            if self._changed_list:
                # print("cobj")
                pass
                {% for prop in obj.lists %}
                if self.{{prop.alias}}._copied:
                    #means the list was modified
                    if "{{prop.name_camel}}" in ddict:
                        ddict.pop("{{prop.name_camel}}")
                    ddict["{{prop.name_camel}}"]=[]
                    for item in self.{{prop.name}}._inner_list:
                        if self.{{prop.name}}.schema_property.pointer_type is not None:
                            #use data in stead of rich object
                            item = item._data
                        ddict["{{prop.name_camel}}"].append(item)
                {% endfor %}

        
            if self._changed_prop:
                pass
                {% for prop in obj.properties %}        
                #convert jsobjects to capnpbin data
                if "{{prop.name_camel}}" in self._changed_items:
                    {% if prop.jumpscaletype.NAME == "jsobject" %}
                    ddict["{{prop.name_camel}}"] = self._changed_items["{{prop.name_camel}}"]._data
                    {% else %}
                    ddict["{{prop.name_camel}}"] = self._changed_items["{{prop.name_camel}}"]
                    {% endif %}
                {% endfor %}
                

            try:
                self.__cobj = self._capnp_schema.new_message(**ddict)
            except Exception as e:
                msg="\nERROR: could not create capnp message\n"
                try:
                    msg+=j.data.text.indent(j.data.serializer.json.dumps(ddict,sort_keys=True,indent=True),4)+"\n"
                except:
                    msg+=j.data.text.indent(str(ddict),4)+"\n"
                msg+="schema:\n"
                msg+=j.data.text.indent(str(self._schema.capnp_schema),4)+"\n"
                msg+="error was:\n%s\n"%e
                raise RuntimeError(msg)

            self._changed_reset()

        return self.__cobj

    @property
    def _data(self):        
        try:
            self._cobj.clear_write_flag()
            return self._cobj.to_bytes_packed()
        except:
            self.__cobj=self.__cobj.as_builder()
            return self._cobj.to_bytes_packed()

    def _from_dict(self,ddict):
        """
        update internal data object from ddict
        """
        self.__cobj.from_dict(ddict)
        self._changed_reset()


    def _changed_reset(self):
        if self._changed_prop_permanent:
            return
        self._changed_list = False
        self._changed_prop = False
        self._changed_items = {}
        {% for ll in obj.lists %}    
        self.{{ll.alias}} = List0(self,self._cobj.{{ll.name_camel}}, self._schema.property_{{ll.name}})
        {% endfor %}
        
        
    @property
    def _ddict(self):
        d={}
        {% for prop in obj.properties %}
        {% if prop.jumpscaletype.NAME == "jsobject" %}
        d["{{prop.name}}"] = self.{{prop.alias}}._ddict
        {% else %}
        d["{{prop.name}}"] = self.{{prop.alias}}
        {% endif %}    
        {% endfor %}

        {% for prop in obj.lists %}
        #check if the list has the right type
        if isinstance(self.{{prop.alias}}, List0):
            d["{{prop.name}}"] = self.{{prop.alias}}.pylist()
        else:
            d["{{prop.name}}"] = self.{{prop.alias}}
        {% endfor %}
        if self.id is not None:
            d["id"]=self.id
        return d

    @property
    def _ddict_hr(self):
        """
        human readable dict
        """
        d={}
        {% for prop in obj.properties %}
        {% if prop.jumpscaletype.NAME == "jsobject" %}
        d["{{prop.name}}"] = self.{{prop.alias}}._ddict_hr
        {% else %}
        d["{{prop.name}}"] = {{prop.js_typelocation}}.toHR(self.{{prop.alias}})
        {% endif %}
        {% endfor %}
        {% for prop in obj.lists %}
        #check if the list has the right type
        if isinstance(self.{{prop.alias}}, List0):
            d["{{prop.name}}"] = self.{{prop.alias}}.pylist(ddict=False)
        else:
            d["{{prop.name}}"] = self.{{prop.alias}}
        {% endfor %}
        if self.id is not None:
            d["id"]=self.id
        return d

    def _ddict_hr_get(self,exclude=[],maxsize=100):
        """
        human readable dict
        """
        d = {}
        {% for prop in obj.properties %}
        {% if prop.jumpscaletype.NAME == "jsobject" %}
        d["{{prop.name}}"] = self.{{prop.alias}}._ddict_hr
        {% else %}
        res = {{prop.js_typelocation}}.toHR(self.{{prop.alias}})
        if len(str(res))<maxsize:
            d["{{prop.name}}"] = res
        {% endif %}
        {% endfor %}
        if self.id is not None:
            d["id"] = self.id
        for item in exclude:
            if item in d:
                d.pop(item)
        return d

    def _hr_get(self,exclude=[]):
        """
        human readable test format
        """
        out = "\n"
        res = self._ddict_hr_get(exclude=exclude)
        for key, item in res.items():
            out += "%-20s: %s\n" % (key, item)
        return out

    @property
    def _json(self):
        return j.data.serializer.json.dumps(self._ddict)

    @property
    def _msgpack(self):
        return j.data.serializer.msgpack.dumps(self._ddict)

    def __str__(self):
        return j.data.serializer.json.dumps(self._ddict_hr,sort_keys=True, indent=True)

    __repr__ = __str__
