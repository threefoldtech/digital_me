from Jumpscale import j

p = j.tools.prefab.local
p.runtimes.pip.install("dnslib,nameparser,gevent,unidecode")

# j.servers.zdb.build()

j.clients.zdb.test()

j.data.schema.test()

j.data.bcdb.test()

j.data.types.date.test()
j.data.types.numeric.test()


if p.platformtype.isLinux:
    j.servers.dns.test()